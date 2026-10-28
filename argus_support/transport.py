"""Bounded HTTP/local transport with content-checked cache and request receipts."""
import hashlib
import datetime
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


class Transport:
    def __init__(self, cache=None, offline=False, retries=2, timeout=20,
                 budget=128_000_000, max_requests=200, max_response=16_000_000):
        self.cache = Path(cache) if cache else None
        self.offline, self.retries, self.timeout = offline, retries, timeout
        self.budget, self.max_requests, self.max_response = budget, max_requests, max_response
        self.bytes = self.requests = 0
        self.receipts = []
        if self.cache:
            self.cache.mkdir(parents=True, exist_ok=True)

    def get(self, url, method='GET'):
        token = hashlib.sha256((method+' '+url).encode()).hexdigest()
        path = self.cache / (token+'.json') if self.cache else None
        if path and path.exists():
            receipt = json.loads(path.read_text())
            raw = (self.cache / (token+'.bin')).read_bytes()
            if hashlib.sha256(raw).hexdigest() != receipt['sha256']:
                raise ValueError('Cache checksum mismatch')
            if receipt['url'] != url or receipt['method'] != method:
                raise ValueError('Cache identity mismatch')
            self.receipts.append({**receipt, 'cache_hit': True})
            return receipt['status'], raw
        if url.startswith(('http://', 'https://')):
            if self.offline:
                raise OSError('OFFLINE_CACHE_MISS')
            for attempt in range(self.retries+1):
                if self.requests >= self.max_requests:
                    raise OSError('REQUEST_BUDGET_EXHAUSTED')
                if method == 'GET' and self.bytes >= self.budget:
                    raise OSError('BYTE_BUDGET_EXHAUSTED')
                self.requests += 1
                try:
                    req = urllib.request.Request(url, method=method,
                        headers={'User-Agent': 'argus-surface-support/0.1'})
                    with urllib.request.urlopen(req, timeout=self.timeout) as response:
                        status = response.status
                        raw = b'' if method == 'HEAD' else response.read(
                            min(self.max_response, self.budget-self.bytes)+1)
                    self.bytes += len(raw)
                    if len(raw) > self.max_response or self.bytes > self.budget:
                        raise ValueError('RESPONSE_OR_BYTE_BUDGET_EXCEEDED')
                    if status != 200:
                        raise ValueError('Unexpected HTTP success status '+str(status))
                    break
                except urllib.error.HTTPError as exc:
                    if exc.code == 404:
                        status, raw = 404, b''
                        break
                    self.receipts.append({'url': url, 'method': method,
                        'status': exc.code, 'attempt': attempt+1})
                    if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == self.retries:
                        raise
                except (OSError, TimeoutError) as exc:
                    self.receipts.append({'url': url, 'method': method,
                        'error': type(exc).__name__+': '+str(exc), 'attempt': attempt+1})
                    if attempt == self.retries:
                        raise
                time.sleep(min(2**attempt, 4))
        else:
            source = Path(url)
            if not source.is_file():
                status, raw = 404, b''
            else:
                status = 200
                if method == 'HEAD':
                    raw = b''
                else:
                    with source.open('rb') as stream:
                        raw = stream.read(min(self.max_response, self.budget-self.bytes)+1)
                    self.bytes += len(raw)
                    if len(raw) > self.max_response or self.bytes > self.budget:
                        raise ValueError('RESPONSE_OR_BYTE_BUDGET_EXCEEDED')
        receipt = {'url': url, 'method': method, 'status': status,
                   'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                   'fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        self.receipts.append({**receipt, 'cache_hit': False})
        if path:
            (self.cache / (token+'.bin')).write_bytes(raw)
            path.write_text(json.dumps(receipt), encoding='utf8')
        return status, raw
