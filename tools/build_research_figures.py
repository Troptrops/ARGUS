"""Rebuild scientific figures only from independently replayed captured data."""
from pathlib import Path
import json,hashlib,shutil,struct
import blosc2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT=Path(__file__).resolve().parent
P=ROOT.parent
F=P/'figures'
TEAL='#157c83'; ORANGE='#c26337'; INK='#193842'; GRAY='#afbbc1'; PALE='#eef3f4'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,
    'axes.labelcolor':INK,'text.color':INK,'axes.spines.top':False,'axes.spines.right':False})
data=json.loads((P/'evidence/REVIEW_RECOMPUTED_2026_10_23.json').read_text())
h=data['heldout']; cells=h['cells']
import zipfile
with zipfile.ZipFile(P/'ARGUS_04_HELDOUT_CAPTURE.zip') as capture:
    raw=capture.read('raw/96_32_23.blosc')
arr=np.frombuffer(blosc2.decompress(raw),dtype=np.uint8).reshape(192,192,192)
positive=arr!=0
gap=np.zeros_like(positive);gap[128:,:,:]=True
stored=positive&~gap; absent=positive&gap
records=[]


def save(fig,name,caption):
    fig.savefig(F/(name+'.png'),dpi=170,bbox_inches='tight',facecolor='white')
    fig.savefig(F/(name+'.svg'),bbox_inches='tight',facecolor='white')
    plt.close(fig)
    records.append({'figure':name,'caption':caption,'basis':'Archived source bytes and local CT-object receipts; no live reacquisition',
        'h11_compressed_sha256':hashlib.sha256(raw).hexdigest() if 'H11' in name else None})


def main():
    F.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(2,1,figsize=(10.5,5.9),height_ratios=[1,3],layout='constrained')
    axes[0].barh([0],[h['positive_in_stored_ct']],color=TEAL)
    axes[0].barh([0],[h['positive_in_absent_ct']],left=[h['positive_in_stored_ct']],color=ORANGE)
    axes[0].set_xlim(0,h['positive_voxels']);axes[0].set_yticks([])
    axes[0].set_xticks([0,5e6,10e6,15e6,19_932_389],['0','5m','10m','15m','19,932,389'])
    axes[0].set_title('Full sampled prediction chunks: 11,412,777 stored-region + 8,519,612 absent-region positives')
    for row in cells:
        index=int(row['id'][1:]); y=2-index//8;x=index%8
        frac=row['positive_in_absent_ct']/row['total_positive'] if row['total_positive'] else None
        color=GRAY if row['prediction_status']=='ABSENT_404' else ORANGE if frac else TEAL
        axes[1].add_patch(plt.Rectangle((x-.45,y-.28),.9,.56,color=color))
        label=row['id']+'\n'+('no object' if frac is None else f'{100*frac:.1f}% gap')
        axes[1].text(x,y,label,ha='center',va='center',fontsize=11,color='white' if frac is not None else INK)
    axes[1].legend(handles=[Patch(color=TEAL,label='0% gap'),Patch(color=ORANGE,label='Some gap'),Patch(color=GRAY,label='Prediction object absent')],loc='lower center',bbox_to_anchor=(.5,-.18),ncol=3,fontsize=10,frameon=False)
    axes[1].set_xlim(-.6,7.6);axes[1].set_ylim(-.5,2.5);axes[1].set_xticks([])
    axes[1].set_yticks([2,1,0],['Z chunks 92-94','95-97','98-100'])
    axes[1].set_title('All 24 selected cells retained; percentages use each stored cell\'s positive-label denominator')
    fig.suptitle('Local PHerc0211 storage audit: 42.742553% of 19,932,389 positive labels',fontweight='bold')
    save(fig,'01_HELDOUT_FINDING','Thirteen stored prediction chunks, eleven absent. Positive-weighted ratio in this local full-chunk sample only; not scroll prevalence or physical papyrus absence.')

    fig,axes=plt.subplots(1,3,figsize=(10.5,3.8),layout='constrained')
    for ax,mask,title in zip(axes,[positive,stored,absent],['All positive labels','In stored CT-chunk regions','In absent CT-chunk regions']):
        im=ax.imshow(mask.sum(axis=0),origin='lower',vmin=0,vmax=int(positive.sum(axis=0).max()),cmap='viridis',interpolation='nearest')
        ax.set_title(title,fontsize=11);ax.set_xlabel('Local X (voxel index)');ax.set_ylabel('Local Y (voxel index)')
    fig.colorbar(im,ax=axes,label='Positive labels along Z per YX pixel (shared linear scale)',shrink=.8)
    fig.suptitle('H11 source-label projections - not CT intensity images',fontweight='bold')
    save(fig,'02_ACTUAL_VOXEL_CASE_H11','Original decoded prediction-label counts projected along Z, partitioned using the archived CT-object receipt states. Counts per YX pixel can include multiple Z positions.')

    six=[r for a in data['six_case_archives'] for r in a['cases']]
    fig,ax=plt.subplots(figsize=(9.5,4.6),layout='constrained')
    y=np.arange(6);a=np.array([r['positive_in_stored_ct'] for r in six]);b=np.array([r['positive_in_absent_ct'] for r in six])
    ax.barh(y,a,color=TEAL,label='In stored CT-chunk regions');ax.barh(y,b,left=a,color=ORANGE,label='In absent CT-chunk regions')
    ax.set_yticks(y,[r['id']+(' (flagged)' if i<2 else ' (comparator)') for i,r in enumerate(six)])
    for i,r in enumerate(six):ax.text(r['total_positive']+50_000,i,f"{r['total_positive']:,}",va='center',fontsize=10)
    ax.set_xlim(0,5_000_000);ax.invert_yaxis();ax.set_xlabel('Nonzero prediction labels (voxels)')
    ax.ticklabel_format(axis='x',style='plain');ax.legend(loc='lower right',fontsize=9)
    ax.set_title('Six selected examples: descriptive contrast, not classification accuracy')
    save(fig,'03_SELECTED_CASES_DESCRIPTIVE','Outcome-conditioned earlier examples: 5,223,732 absent-region positives across two flagged cases and 6,520,264 stored-region positives across four comparators. Not pooled with the 24-cell survey.')

    for name,title,labels in [
      ('04_METHOD_AND_VALIDITY_GATES','Evidence levels: only the first two are established here',[
       '1  Prediction labels\nOriginal bytes decoded','2  CT-object states\nArchived HTTP receipts','3  Physical CT support\nNOT ESTABLISHED','4  Papyrus geometry\nNOT ESTABLISHED','5  Ink / writing\nNOT ESTABLISHED']),
      ('08_ARGUS_WHY_IT_MATTERS','Proposed researcher use: make one review decision traceable',[
       'Preserve\nSource bytes + hashes','Locate\nNominal index partitions','Flag\nStorage-state discrepancy','Inspect\nTransforms and source CT','Decide\nDocument a user action'])]:
        fig,ax=plt.subplots(figsize=(11,2.7),layout='constrained');ax.axis('off')
        for i,label in enumerate(labels):
            x=.02+i*.197
            ax.add_patch(plt.Rectangle((x,.30),.18,.48,facecolor=PALE if i<2 else '#fff0e8',edgecolor=TEAL if i<2 else ORANGE))
            ax.text(x+.09,.54,label,ha='center',va='center',fontsize=10)
            if i<4:ax.text(x+.188,.54,'>',ha='center',va='center',fontsize=14)
        ax.text(.5,.10,'Nominal index correspondence is not independently verified physical registration.',ha='center',fontsize=11)
        ax.set_title(title,fontweight='bold',pad=12)
        save(fig,name,'Explanatory schematic, not additional measurement. Downstream utility is proposed and has not been demonstrated by a researcher intervention.')

    milestones=[('Benchmark','Nov 2-6'),('Registration','Nov 9-13'),('User decision','Nov 16-20'),('Transfer','Nov 23-30'),('Reproduction','Dec 1-11'),('Maintain / upstream / retire','Dec 14-18')]
    fig,ax=plt.subplots(figsize=(10,3.6),layout='constrained');ax.axis('off')
    for i,(work,date) in enumerate(milestones):
        yy=.86-i*.14;ax.text(.02,yy,date,weight='bold');ax.text(.22,yy,work)
        ax.text(.58,yy,['Matched full-workflow comparison','Verified / failed / unresolved','One documented downstream action','Frozen independent area; retain failures','Clean platforms; volunteer replay','Evidence-based release decision'][i],fontsize=10)
    ax.set_title('Conditional November-December critical path - future work',fontweight='bold')
    save(fig,'05_NOV_DEC_CRITICAL_PATH','All milestones are conditional proposals. Registration failure restricts interpretation to storage states; equivalent prior-art functionality triggers an upstream or retirement decision.')

    fig=plt.figure(figsize=(10.5,5.3),layout='constrained');grid=fig.add_gridspec(2,2,width_ratios=[1,1])
    ax=fig.add_subplot(grid[:,0],projection='3d')
    points=np.argwhere(stored)[::24]
    ax.scatter(points[:,2],points[:,1],points[:,0],s=.8,color=TEAL,alpha=.5,rasterized=True)
    lo=[0,176,128];hi=[192,192,192]
    vertices=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
    faces=[[vertices[j] for j in ids] for ids in ([0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5])]
    ax.add_collection3d(Poly3DCollection(faces,facecolor=ORANGE,edgecolor=ORANGE,alpha=.25))
    ax.set(xlim=(0,192),ylim=(0,192),zlim=(0,192),xlabel='Local X',ylabel='Local Y',zlabel='Local Z')
    ax.set_title('3D locator only: sampled labels + exact index-cell cuboid',fontsize=10)
    for row,z in enumerate((8,150)):
        axis=fig.add_subplot(grid[row,1]);plane=np.zeros((192,192),dtype=np.uint8)
        plane[stored[z]]=1;plane[absent[z]]=2
        axis.imshow(plane,origin='lower',cmap=ListedColormap(['#f4f5f5',TEAL,ORANGE]),vmin=0,vmax=2,interpolation='nearest')
        axis.set_title(f'Original prediction labels at local Z={z}',fontsize=11)
        axis.set_xlabel('Local X (voxel index)');axis.set_ylabel('Local Y (voxel index)')
        if z==150:
            axis.axhline(175.5,color=ORANGE,ls='--',lw=1)
            axis.text(5,158,'Y=176: label-slab edge',fontsize=8,color=ORANGE)
    fig.suptitle('H11: 279,426 positive labels; 196,608 mapped to absent storage',fontweight='bold')
    save(fig,'06_H11_EXPLAINED_WITH_ORIGINAL_SLICES','Teal: 82,818 positives in stored CT-chunk regions. Orange: 196,608 positives in absent regions. Y=176 is the label-slab edge; the CT storage transition is Z=128. The 3D locator is not papyrus anatomy.')

    fig,axes=plt.subplots(1,2,figsize=(10.5,4.1),width_ratios=[1.6,1],layout='constrained')
    z=np.arange(192);axes[0].bar(z,stored.sum(axis=(1,2)),color=TEAL,width=1,label='Stored-region positives')
    axes[0].bar(z,absent.sum(axis=(1,2)),bottom=stored.sum(axis=(1,2)),color=ORANGE,width=1,label='Absent-region positives')
    axes[0].axvline(127.5,color=INK,ls='--',lw=1);axes[0].text(132,4400,'CT storage transition\nat local Z=128',fontsize=10)
    axes[0].set(xlabel='Local Z (voxel index)',ylabel='Nonzero labels per Z plane',xlim=(-.5,191.5),ylim=(0,5500))
    axes[0].legend(fontsize=9);axes[1].axis('off')
    axes[1].text(0,.93,'Exact half-open bounds (Z,Y,X)',weight='bold')
    axes[1].text(0,.72,'[128,192) x [176,192) x [0,192)\n\n64 x 16 x 192 = 196,608',fontsize=13)
    axes[1].text(0,.35,'Every voxel in that block is positive.\nIt equals the absent-storage positive mask.\nThe full positive mask also contains\n82,818 stored-region labels.',fontsize=10,linespacing=1.6)
    fig.suptitle('H11 exact slab verification - original label array, not CT anatomy',fontweight='bold')
    save(fig,'07_H11_EXACT_SLAB_RAW_DATA_PROOF','Each high-Z slab plane has 3,072 positive labels; 64 such planes total 196,608. The slab is present before 3x max-pool mesh coarsening. Its causal or physical significance is unresolved.')

    text='# Reviewed figure captions\n\n'
    for record in records:text+='## '+record['figure']+'\n\n'+record['caption']+'\n\n'
    text+='Source: Vesuvius Challenge PHerc0211 m7 surface-prediction labels, original captured Blosc chunks, and local masked-CT HEAD receipts. All axes use voxel indices or label counts, never verified physical millimeters. Data terms are separate from software MIT. No figure establishes papyrus, physical registration or ink.\n'
    (F/'FIGURE_CAPTIONS.md').write_text(text,encoding='utf8')
    (F/'06_07_H11_FIGURE_CAPTIONS_AND_LIMITS.md').write_text('# H11 corrected captions\n\n'+records[-2]['caption']+'\n\n'+records[-1]['caption']+'\n',encoding='utf8')
    (F/'FIGURE_PROVENANCE.json').write_text(json.dumps({'review_date':'2026-10-23','generator':'tools/build_research_figures.py','records':records},indent=2)+'\n')
    models=[]
    for p in (P/'05_3D_AND_CLIPPING').glob('*.glb'):
        raw=p.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length])
        models.append({'file':p.name,'sha256':hashlib.sha256(raw).hexdigest(),
            'position_accessors':[{'min':a.get('min'),'max':a.get('max'),'count':a['count']} for a in doc['accessors'] if a['type']=='VEC3'],
            'classification':'coarse prediction-label locator; not quantitative or anatomical geometry'})
    (P/'05_3D_AND_CLIPPING/REVIEWED_MODEL_LIMITS.json').write_text(json.dumps({'models':models,
       'exact_absent_positive_bounds_local_zyx':[[128,192],[176,192],[0,192]],
       'coarse_orange_glb_bounds_local_xyz':[[0,192],[174,192],[126,192]],
       'edge_expansion_warning':'3x ANY/max pooling expands coarse label support; do not measure source slab extents from GLB',
       'interactive_test':'static code/asset inspection only; browser interaction not validated'},indent=2)+'\n')
    print('Regenerated figures',len(records))


if __name__=='__main__':main()
