"""Create the reviewed dossier and conditional proposal brief with reportlab."""
from pathlib import Path
import re,html
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
INTRO="I'm Spencer Tropea, an independent creator and researcher from Ontario, Canada. My background is in communications, and my interests in history and literature led me to the possibility of recovering writing thought lost for centuries.\n\nARGUS began with that possibility and a practical question: how do we know that what our software shows is supported by the evidence? I have developed it iteratively with AI-assisted software development, open-source research, experimental tests and separate checks of captured data. I am contributing an audit workflow, learning from techniques and expertise established by others.\n\nThe name recalls Argus Panoptes, the many-eyed watcher of Greek mythology: a reminder to inspect carefully and keep uncertainty visible.\n\nThese scrolls were once people's words and possessions. I found myself wanting, symbolically, to ask their permission to look; for me, that means approaching their surviving intellectual lives with care, without a sense of entitlement.\n\nI welcome scientific criticism, independent reproduction and collaboration. My aim is to help preserve knowledge through useful, accountable work, wherever that contribution belongs in the existing research community."

P=Path(__file__).resolve().parents[1];F=P/'figures'
INK=colors.HexColor('#183842');TEAL=colors.HexColor('#157c83');ORANGE=colors.HexColor('#b85d34');PALE=colors.HexColor('#edf3f3')
font='Helvetica';bold='Helvetica-Bold'
if Path('C:/Windows/Fonts/arial.ttf').exists():
    pdfmetrics.registerFont(TTFont('ReviewArial','C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('ReviewArialBold','C:/Windows/Fonts/arialbd.ttf'))
    pdfmetrics.registerFontFamily('ReviewArial',normal='ReviewArial',bold='ReviewArialBold',italic='ReviewArial',boldItalic='ReviewArialBold')
    font='ReviewArial';bold='ReviewArialBold'
styles={
 'title':ParagraphStyle('title',fontName=bold,fontSize=24,leading=28,textColor=INK,spaceAfter=12),
 'heading':ParagraphStyle('heading',fontName=bold,fontSize=17,leading=21,textColor=INK,spaceAfter=10),
 'sub':ParagraphStyle('sub',fontName=bold,fontSize=11,leading=15,textColor=TEAL,spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('body',fontName=font,fontSize=10.3,leading=15,textColor=INK,spaceAfter=9),
 'small':ParagraphStyle('small',fontName=font,fontSize=8.5,leading=12,textColor=INK,spaceAfter=6),
 'caption':ParagraphStyle('caption',fontName=font,fontSize=8.5,leading=12,textColor=INK,spaceAfter=10),
 'cell':ParagraphStyle('cell',fontName=font,fontSize=9,leading=12,textColor=INK),
 'code':ParagraphStyle('code',fontName='Courier',fontSize=8,leading=11,textColor=INK,spaceAfter=7)}


def clean(s):
    return s.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-').replace('\u00d7','x')


def para(s,style='body'):
    return Paragraph(clean(s),styles[style])


def plain(s,style='body'):
    return para(html.escape(s),style)


def picture(name,width=492):
    from PIL import Image as PILImage
    path=F/name
    with PILImage.open(path) as img:w,h=img.size
    return Image(str(path),width=width,height=width*h/w)


def table(rows,widths,header=True):
    t=Table([[plain(str(c),'cell') for c in row] for row in rows],colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),
        ('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[PALE,colors.white]),('LINEBELOW',(0,0),(-1,0),.6,TEAL)]))
    if header:t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfecec'))]))
    return t


def note(s):
    t=Table([[para(s,'small')]],colWidths=[492])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.4,TEAL),
       ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
       ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return t


def frame(c,doc):
    w,h=A4;c.saveState();c.setStrokeColor(colors.HexColor('#b6ccce'));c.line(48,h-45,w-48,h-45)
    c.setFont(bold,9);c.setFillColor(TEAL);c.drawString(48,h-33,'ARGUS  /  SURFACE SUPPORT')
    c.setFont(font,8);c.setFillColor(INK);c.drawRightString(w-48,h-33,'SPENCER TROPEA  |  SOURCE RELEASE 0.4.3')
    c.line(48,43,w-48,43);c.setFont(font,8);c.drawString(48,30,'28 October 2026  |  Archived storage-state evidence  |  Not submitted')
    c.drawRightString(w-48,30,f'{doc.page:02}');c.restoreState()


def build(path,story):
    doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=62,bottomMargin=58,
        title='ARGUS Surface Support - reviewed research dossier' if 'DOSSIER' in path.name else 'ARGUS November-December conditional proposal',
        author='Spencer Tropea',subject='Prediction labels and masked-CT storage; physical registration unverified')
    doc.build(story,onFirstPage=frame,onLaterPages=frame)


def main():
    s=[]
    s += [para('What the archived evidence supports','title'),
      para('A reproducible local audit of prediction labels and masked-CT storage','sub'),
      plain('Computational surface predictions can be read more confidently than their source-data support justifies. ARGUS makes a limited part of that relationship inspectable: positive prediction labels versus masked-CT chunk storage on nominal matching indices.'),
      table([['Selected local cells','Positive prediction labels','In absent masked-CT storage'],['24 (13 stored, 11 absent)','19,932,389','8,519,612 / 42.742553%']],[148,167,177]),Spacer(1,10),
      picture('01_HELDOUT_FINDING.png'),
      plain('Method: decode captured original label chunks; derive each CT-chunk intersection; reconcile storage states with archived HTTP receipts; retain all sampled cells and the denominator. The six earlier selected examples are reported separately.','small'),
      note('<b>Claim limit:</b> these are label/storage observations. Missing masked storage does not establish missing original CT, invalid papyrus, physical registration, ink or writing. The percentage is local and positive-voxel weighted, not whole-scroll prevalence.'),
      PageBreak()]
    s += [para('Why I began ARGUS','heading')]
    for paragraph in INTRO.split('\n\n'):s.append(plain(paragraph))
    s += [Spacer(1,4),para('A practical contribution, open to correction','sub'),
      plain('The work was developed with AI-assisted software tools and existing open-source research. Separate counting implementations agree on these archived inputs; no external researcher reproduction, institutional endorsement or server attestation is claimed.'),
      picture('04_METHOD_AND_VALIDITY_GATES.png'),
      plain('Established here: original prediction-label counts and archived masked-CT storage states. Physical CT support, verified sheet geometry and ink identification remain separate evidence gates.','caption'),
      PageBreak()]
    s += [para('The 24-cell local survey','heading'),
      plain('The deterministic plan regenerates from 423 eligible prediction cells intersecting the historically selected R04 halo, excluding 18 prior survey keys. Eight cells are hash-ranked within each of three fixed Z strata. The archived hash verifies content; it does not independently prove when the plan was fixed or rule out historical outcome-peeking.'),
      table([['Z chunk stratum','Stored / absent predictions','Positive labels','In absent CT storage'],
        ['92-94','7 / 1','9,332,548','2,789,605'],['95-97','6 / 2','10,599,841','5,730,007'],['98-100','0 / 8','0','0']],[105,135,120,132]),
      Spacer(1,12),plain('All 24 selected locations and 186 distinct CT keys were accounted for. The archive contains 212 request receipts: 26 prediction/metadata GETs and 186 CT HEADs. CT receipts record 75 stored and 111 absent objects.'),
      picture('02_ACTUAL_VOXEL_CASE_H11.png'),
      plain('H11 projections illustrate source-label content, not CT anatomy. Color intensity is a count of positive labels along Z per YX pixel. Source: unchanged original H11 Blosc bytes, SHA256 recorded with the figure.','caption'),
      note('Counts use FULL 192-cubed prediction chunks selected for intersecting the halo. They are not halo-clipped or R12-specific. Spatial dependence and the historical frame prevent a whole-scroll or classifier-performance inference.'),PageBreak()]
    s += [para('H11: the block is in the label array','heading'),
      picture('06_H11_EXPLAINED_WITH_ORIGINAL_SLICES.png'),
      plain('Original prediction chunk 96/32/23 contains 279,426 positive labels: 82,818 in stored CT-chunk regions and 196,608 in absent regions. Exactly the absent-region positive mask equals local Z[128,192), Y[176,192), X[0,192). The full positive mask also includes the 82,818 other labels.','caption'),
      picture('07_H11_EXACT_SLAB_RAW_DATA_PROOF.png'),
      plain('Correction: Y=176 is the label slab edge. The archived CT-object transition is at local Z=128. Coarse 3D models can expand edges through max pooling; the original voxel array, not the model, establishes the exact count and bounds. Cause and physical significance remain unresolved.','caption'),PageBreak()]
    s += [para('Descriptive cases and prior art','heading'),
      picture('03_SELECTED_CASES_DESCRIPTIVE.png'),
      plain('The six earlier cases were selected after preliminary observations. Two flagged chunks contribute 5,223,732 absent-region positives; four contrasting comparators contribute 6,520,264 stored-region positives. They demonstrate counting behavior and must not be pooled with the new survey to estimate rates.'),
      para('Complementary value must be demonstrated','sub'),
      plain('Schurkai\'s vesuvius-phantom-audit already offers scroll-wide chunk audits, voxel-level checks and cleanup. A matched comparison of its pinned pure overlap function with ARGUS agrees at all 24 sampled cells. This establishes overlap in functionality; it is not a full runtime or end-to-end benchmark.'),
      table([['Existing capability','ARGUS candidate addition / limit'],['Chunk and voxel checks; cleanup','Compact fixed-sample acquisition, local receipts and replayable partitions'],['Native CT intensity checks in upstream cleanup','Current submission uses object states; no independently registered CT-intensity validation'],['Published upstream code','Reviewed source release; no demonstrated adoption or practical superiority']],[215,277]),
      plain('Pinned prior-art commit: ab9ace908a1644c32ce0206e3eecfefba2c4bc81. Function agreement is recorded in docs/UPSTREAM_SOURCE_RECORD.json and the prior local review. No new defect category or superiority is claimed.','small'),PageBreak()]
    s += [para('Technical review: fixes and limits','heading'),
      table([['Review finding','Revised behavior'],
       ['Oversize/budget errors could return stale HTTP 200','Failed bodies remain unknown; regression tests pass'],
       ['Capture/error output could overwrite evidence','Exclusive creation and separate diagnostic ZIP'],
       ['Unknown state and duplicate partition risks','Unknown normalization; disjointness and partial-state checks'],
       ['Conflicting versions and missing commands','Reviewed source 0.4.3; three documented capture replays'],
       ['Misleading figure boundary and mask property','Correct Z=128 storage transition; precise slab-mask equality']],[215,277]),
      Spacer(1,12),plain('The received nine tests pass; the reviewed source passes 16 tests on Windows Python 3.12.14 with NumPy and Blosc2. The supplied row-wise verifier and a separately implemented review audit reproduce the central totals. Tests do not certify every inherited library path or substitute for clean-platform checks.'),
      para('Reproducibility has a defined scope','sub'),
      plain('Source compressed bytes, metadata fingerprints, local receipt records, deterministic selection and per-intersection counts are available for replay. SHA256 establishes internal consistency, not a third-party signature or a proof of capture chronology. Physical registration remains unverified.'),
      para('Code and data have different rights','sub'),
      plain('Original ARGUS software carries an MIT grant. The AWS Vesuvius CT registry identifies CC BY-NC 4.0 data; exact prediction-asset notices must be checked before public redistribution. Original source data, derived figures and models are not relicensed by the software grant.'),
      note('Clean Windows/Linux Python 3.11 and 3.13 checks are configured in CI; see docs/VALIDATION.md and the exact commit checks for their actual status. A full upstream benchmark, demonstrated user benefit, physical registration and external researcher reproduction remain open.'),PageBreak()]
    s += [para('November-December: conditional progress','heading'),
      plain('The aim is one useful, maintained capability in the existing research ecosystem. These are proposed milestones, not promises of discovery or completed community integration.'),
      table([['Window','Deliverable / decision gate'],['Nov 2-6','Matched end-to-end benchmark; distinguish useful addition from duplication'],['Nov 9-13','Independent transforms and mask-semantics review: verified / failed / unresolved'],['Nov 16-20','One traceable downstream inspection or processing decision'],['Nov 23-30','Frozen independent region/scroll; preserve all failures and denominators'],['Dec 1-11','Clean platforms, schema and resource checks; invite volunteer replay'],['Dec 14-18','Technical note and maintain / upstream / retire decision'],['Dec 21-31','Buffer for documentation, feedback and maintenance']],[100,392]),
      Spacer(1,10),para('Opportunities for Collaboration','sub'),
      plain('Review the prediction-to-CT assumptions; reproduce H11 or one fixed case; test another dataset; recommend an existing workflow integration point; advise whether receipt or partition exports belong upstream.'),
      note('If registration fails, preserve only storage-state claims. If an existing tool supplies equivalent value, prefer an upstream contribution or retire duplication. R12 stays outside this critical path and Gate 7F remains blocked.'),
      plain('I welcome scientific criticism, independent reproduction and collaboration. No endorsement, private data access, computing allocation or appointment is requested.'),PageBreak()]
    s += [para('Reproduce the public source release','heading'),
      plain('From the repository root, install the verification extra and replay the retained historical capture. Offline replay makes no network requests. The README documents the historical capture rights limits and all three counting commands.'),
      plain('python -m pip install ".[verification]"','code'),
      plain('Input: ARGUS_04_HELDOUT_CAPTURE.zip (the unchanged historical capture)','small'),
      plain('python -O tools/review_release.py ARGUS_04_HELDOUT_CAPTURE.zip --out REPLAY','code'),
      plain('python -m unittest discover -s tests -v','code'),
      para('Source release and research limits','sub'),
      plain('Reviewed source is prepared for the existing Troptrops/ARGUS repository. Source, protocol, reports and figures can be inspected individually. The README and CI report exact release status; a full benchmark and one downstream user decision would strengthen the prize case. Asset-specific prediction rights remain unresolved; no new raw data is introduced.'),
      plain('The author authorized source publication. Competition submission and outreach are separate decisions and have not been performed here. Source publication does not establish scientific acceptance or an award. Historical capture preservation is not a blanket grant to redistribute prediction bytes.'),
      para('Sources and attribution','sub'),
      para('<b>Dataset:</b> Vesuvius Challenge - CT Scans of Herculaneum Papyri. Newer PHerc0211 scan and m7 prediction data, credited to the Vesuvius Challenge creators and maintainers. <link href="https://scrollprize.org/data" color="#157c83">scrollprize.org/data</link>','small'),
      para('<b>Dataset terms:</b> <link href="https://registry.opendata.aws/vesuvius-challenge-herculaneum-scrolls/" color="#157c83">AWS Vesuvius dataset registry</link> (CC BY-NC 4.0; check asset-specific terms).','small'),
      para('<b>Prior work:</b> <link href="https://github.com/Schurkai/vesuvius-phantom-audit" color="#157c83">github.com/Schurkai/vesuvius-phantom-audit</link>; ScrollPrize/villa and their contributors.','small'),
      para('<b>Prize rules and actual form entry point:</b> <link href="https://scrollprize.org/prizes" color="#157c83">scrollprize.org/prizes</link>. Deadline checked 28 October: 31 October 2026, 11:59 pm Pacific.','small'),
      note('Look carefully. Verify what you can. Be honest about what you cannot yet see.'),
      plain('Public repository: https://github.com/Troptrops/ARGUS. Evidence: evidence/; protocol: protocol/; source: argus_support/ and tools/; verification: docs/VALIDATION.md; hashes: FILE_SHA256.txt. Historical reports are marked separately under research/history/.','small')]
    build(P/'research/ARGUS_RESEARCH_DOSSIER.pdf',s)

    s=[para('From an archived result to a useful contribution','title'),
      plain('Spencer Tropea | November-December 2026 | Conditional proposal'),
      plain('October establishes a replayable storage-state observation: 8,519,612 of 19,932,389 positive labels in the sampled stored chunks map to absent masked-CT objects. It does not establish physical registration, papyrus identity or ink.'),
      picture('05_NOV_DEC_CRITICAL_PATH.png'),
      para('Decision policy','sub'),
      plain('Begin with approved, rights-reviewed reproducibility. Compare the existing tools fairly before claiming a missing function. Verify physical coordinates before interpreting material. Demonstrate a user decision before claiming practical impact.'),
      note('If baseline functionality is equivalent, contribute a narrow improvement upstream or stop duplication. If registration fails, publish the failure and retain only storage-state observations. Outcomes and external collaboration cannot be guaranteed.'),PageBreak(),
      para('Milestones with measurable gates','heading'),
      table([['Window','Evidence to produce','Go / no-go decision'],
       ['Oct 23-31','Approved source, tag and fixed-case replay; rights review','Keep private if approval or rights are unresolved'],
       ['Nov 2-6','Matched full-workflow accuracy/agreement, time, memory, bytes and error comparison','Distinct value, upstream pivot or retire'],
       ['Nov 9-13','Authoritative transforms, mask semantics and independent landmarks','Verified / failed / unresolved registration'],
       ['Nov 16-20','One reproducible researcher decision and machine-readable export','Useful workflow or documented usability failure'],
       ['Nov 23-30','Second area frozen before outcomes; complete denominator','Transfer finding or honest access failure'],
       ['Dec 1-11','Clean Windows 3.13/Linux, schema, limits and volunteer replay request','Executed checks separated from untested promises'],
       ['Dec 14-18','Technical note, changelog, feedback and maintenance decision','Maintain / merge upstream / retire'],
       ['Dec 21-31','Documentation and follow-up buffer','No dependency on prize outcome or reviewer availability']],[78,245,169]),
      Spacer(1,10),plain('R12 remains a separate exploratory branch. No ink analysis, letter interpretation or Gate 7F progression is on this critical path.'),PageBreak(),
      para('Opportunities for Collaboration','heading'),
      plain('1. Review the nominal prediction-to-CT coordinate assumptions and point to authoritative transforms.'),
      plain('2. Reproduce H11 or one fixed cell from the original archived compressed bytes.'),
      plain('3. Test the audit on a different approved region or scan with its plan fixed before outcomes.'),
      plain('4. Identify a VC3D/villa or data-QA step where an inspection report would change a real decision.'),
      plain('5. Advise whether compact receipts, deterministic sampling or partition exports belong in phantom-audit upstream.'),
      para('Commitment and constraints','sub'),
      plain('I welcome scientific criticism and independent reproduction. The aim is to contribute something practical and maintainable, wherever it belongs in the existing toolchain. No role, endorsement, allocation or private access is requested.'),
      plain('Keep the CPU-first capture/replay path. Lock inputs, retain negative and unavailable results, and separate proposals from achieved milestones. AI-assisted software development remains disclosed and its outputs require tests and evidence review.'),
      note('A responsible year-end outcome may be a useful small patch, a limited storage-state tool, or a well-documented reason to stop. It is not a guarantee of discovery.'),
      para('References','sub'),
      plain('Official criteria: https://scrollprize.org/prizes\nExisting audit/cleanup: https://github.com/Schurkai/vesuvius-phantom-audit\nData: https://scrollprize.org/data','small')]
    build(P/'research/NOV_DEC_PROPOSAL_BRIEF.pdf',s)
    from pypdf import PdfReader
    for path,expected in [(P/'research/ARGUS_RESEARCH_DOSSIER.pdf',8),(P/'research/NOV_DEC_PROPOSAL_BRIEF.pdf',3)]:
        n=len(PdfReader(path).pages)
        print(path.name,'pages',n,'expected',expected)
        if n!=expected:raise ValueError('Unexpected pagination - inspect overflow')


if __name__=='__main__':main()
