"""Figures for docs/11-feasibility-at-scale.html (synthetic, illustrative)."""
import math, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.family":"serif","font.size":10,"axes.edgecolor":"#888","axes.labelcolor":"#888",
 "xtick.color":"#888","ytick.color":"#888","text.color":"#888","axes.spines.top":False,"axes.spines.right":False,"savefig.transparent":True})
fig,ax=plt.subplots(1,2,figsize=(8.2,3.2))
L=np.logspace(0,7,200); Pstar=1e-4
per=L*(-np.log(0.05/L))/Pstar; pooled=np.full_like(L,-math.log(0.05)/Pstar)
ax[0].loglog(L,per,color="#c0392b",lw=2,label="one bound per cell")
ax[0].loglog(L,pooled,color="#1f4fa3",lw=2,ls="--",label="pooled weighted estimator")
ax[0].axvline(2.56e6,color="#888",lw=.8,ls=":"); ax[0].text(2.56e6*0.7,1e5,"160 HE × 16,000\nlogical scenarios",ha="right",fontsize=8)
ax[0].set_xlabel("number of cells with their own bound, L"); ax[0].set_ylabel("simulation runs for $\\bar P \\leq 10^{-4}$")
ax[0].set_title("(a) per-cell bounds scale with L",fontsize=10); ax[0].legend(frameon=False,fontsize=8,loc="upper left")
d=np.arange(1,101)
for dl,c,ls in [(0.3,"#1f4fa3","-"),(0.5,"#c0392b","--"),(1.0,"#555","-.")]:
    ax[1].semilogy(d,np.exp(-d*dl**2),color=c,ls=ls,lw=2,label=f"IS, shift δ = {dl}")
ax[1].axvspan(4,15,color="#888",alpha=.12); ax[1].text(16,1e-11,"band: cut-in models in the literature",ha="left",fontsize=8)
ax[1].set_ylim(1e-12,1.5); ax[1].set_xlabel("scenario parameters, d"); ax[1].set_ylabel("ESS / N  =  exp(−d δ²)")
ax[1].set_title("(b) IS weights degenerate with d",fontsize=10); ax[1].legend(frameon=False,fontsize=8,loc="upper right")
fig.tight_layout(); fig.savefig("docs/fig/scaling.svg"); print("ok")
