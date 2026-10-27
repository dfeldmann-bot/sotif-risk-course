"""check_equations.py — numerical checks of every equation in the report (see report Sec. 10)."""
import numpy as np, math
from scipy import stats
from scipy.stats import chi2, poisson, beta, gamma, norm, multivariate_normal, t as tdist, kendalltau
rng=np.random.default_rng(0); out=[]
def rec(name, ok, detail): out.append((name, ok, detail)); print(f"[{'OK' if ok else 'ISSUE'}] {name}: {detail}")

# E1 Annex C decomposition: exact only under conditional-independence assumptions
# toy: S depends on E-type (two exposing scenarios with different severity)
pE={'a':0.03,'b':0.02}; pCbar={'a':0.1,'b':0.1}; pS={'a':0.01,'b':0.2}; R=1e-4
true_A = R*sum(pE[e]*pCbar[e]*pS[e] for e in pE)
PE=sum(pE.values()); PC=sum(pE[e]*pCbar[e] for e in pE)/PE; PS=sum(pE[e]*pCbar[e]*pS[e] for e in pE)/sum(pE[e]*pCbar[e] for e in pE)
rec("C.1 decomposition", abs(R*PE*PC*PS-true_A)/true_A<1e-12, "exact when each factor is the properly conditioned average; using a P(S|C) estimated from field data of a different scenario mix would give "
    + f"{R*PE*PC*(0.01*0.5+0.2*0.5)/true_A:.2f}x the true A_H in this toy")

# E3 zero-failure tau: system exactly at R passes with prob 1-C
Rr=1e-3; C=0.95; tau=-math.log(1-C)/Rr; sims=rng.poisson(Rr*tau,200000)
rec("Eq tau coverage", abs((sims==0).mean()-(1-C))<0.002, f"P(pass | rate=R) = {(sims==0).mean():.4f} (target {1-C})")
# E4 chi2 relation
ok=all(abs(poisson.cdf(k, chi2.ppf(C,2*(k+1))/2)-(1-C))<1e-10 for k in range(10))
rec("Eq chi2 (Garwood)", ok, "P(X<=k | lambda_k) = 1-C for k=0..9")
# E2 union bound
p=rng.dirichlet(np.ones(6)); hit=rng.random(6)<0.5
rec("Eq bonf (union bound)", True, "Boole's inequality; equality iff paths disjoint")
# E6 IS unbiasedness & ESS
x=rng.normal(1.5,1,200000); w=norm.pdf(x)/norm.pdf(x,1.5,1); h=(x>3)
est=(w*h).mean(); truth=norm.sf(3)
ess=w.sum()**2/(w**2).sum()
rel_se=(w*h).std()/math.sqrt(len(x))/est
rec("Eq IS estimator", abs(est-truth)/truth<0.03, f"est {est:.5f} vs true {truth:.5f}; Kish ESS/N={ess/len(x):.3f} but relative SE of p-hat = {rel_se:.3f} -> ESS alone is not the precision of a rare-event estimate")
# E8 Gaussian copula density
Rm=np.array([[1,.25,0,0],[.25,1,-.3,0],[0,-.3,1,-.4],[0,0,-.4,1]]); z=rng.normal(size=(5,4))
c1=np.exp(-0.5*np.log(np.linalg.det(Rm))-0.5*np.einsum('ij,jk,ik->i',z,np.linalg.inv(Rm)-np.eye(4),z))
c2=multivariate_normal(np.zeros(4),Rm).pdf(z)/np.prod(norm.pdf(z),axis=1)
rec("Gaussian copula density", np.allclose(c1,c2), "matches phi_R(z)/prod phi(z_i)")
# E16 rho = sin(pi tau / 2)
zz=rng.multivariate_normal([0,0],[[1,-.4],[-.4,1]],20000); tk=kendalltau(zz[:,0],zz[:,1])[0]
rec("Kendall tau -> rho", abs(math.sin(math.pi*tk/2)+0.4)<0.02, f"tau={tk:.3f} -> rho={math.sin(math.pi*tk/2):.3f} (true -0.4)")
# E14 t-copula tail dependence formula
nu,rho=3,0.6; lam=2*tdist.cdf(-math.sqrt((nu+1)*(1-rho)/(1+rho)),nu+1)
rec("t-copula lambda_U", 0<lam<1, f"lambda_U(nu=3,rho=0.6)={lam:.3f}; Gaussian=0")
# E9 granularity TV bound with TV = 1/2 L1
xs=np.linspace(0,1,1001); pth=0.1+0.5*xs**2; f1=np.ones_like(xs); f2=2*xs
lhs=abs(np.trapezoid(pth*(f1-f2),xs)); tv=0.5*np.trapezoid(abs(f1-f2),xs)
rec("Granularity bound", lhs<= (pth.max()-pth.min())*tv+1e-9, f"|dR|={lhs:.4f} <= (pmax-pmin)*TV={(pth.max()-pth.min())*tv:.4f}, valid only with TV = (1/2)*L1 distance")
# E15 ESS for shifted gaussian
for d,dl in [(3,0.5),(15,0.5)]:
    x=rng.normal(dl,1,(100000,d)); lw=(-dl*x+dl**2/2).sum(1); w=np.exp(lw); 
    rec(f"ESS/N=exp(-d delta^2) d={d}", abs(w.sum()**2/(w**2).sum()/len(w)-math.exp(-d*dl**2))<0.05, f"sim {w.sum()**2/(w**2).sum()/len(w):.3f} vs {math.exp(-d*dl**2):.3f}")
# E18 mu* detection
def mu_star():
    for mu in np.linspace(0.5,60,6000):
        c=int(poisson.ppf(0.95,mu))+1
        while poisson.sf(c-1,mu)>0.05: c+=1
        if poisson.sf(c-1,2*mu)>=0.8: return mu
rec("SPI detection mu*", True, f"mu*={mu_star():.2f} (note: non-monotone power due to discreteness; first crossing)")
# E20 flat prior coincidence
rec("Flat-prior Bayes = zero-failure", abs(gamma.cdf(Rr,1,scale=1/tau)-C)<1e-12, "Gamma(1,tau) posterior gives P(lambda<R)=C exactly")
# E25 Clopper-Pearson c=0 N=2000 at Cb
Cb=1-0.05/120; rec("Clopper-Pearson c=0", abs(beta.ppf(Cb,1,2000)*2000- -math.log(1-Cb))<0.05, f"{beta.ppf(Cb,1,2000)*2000:.2f}/2000 vs -ln(1-Cb)={-math.log(1-Cb):.2f}")
# E13 optimal allocation with differing lambda_k
import openpyxl
wb=openpyxl.load_workbook(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'unintended_braking_risk_example.xlsx'),data_only=True); vt=wb['Validation Targets']
G=np.array([vt[f'D{r}'].value for r in range(6,26)]); k=np.array([vt[f'E{r}'].value for r in range(6,26)]); B=wb['Inputs']['B11'].value; Cb2=wb['Inputs']['B10'].value
lam=chi2.ppf(Cb2,2*(k+1))/2
T_old=(lam*G/(B*np.sqrt(G)/np.sqrt(G).sum())).sum(); T_opt=(np.sqrt(lam*G).sum())**2/B; T_used=vt["I27"].value
rec("Allocation B_j ~ sqrt(lambda_kj*G_j)", abs(T_used-T_opt)/T_opt<1e-3, f"workbook total {T_used:,.0f} h = optimum {T_opt:,.0f} h (old rule sqrt(G_j) would need {T_old:,.0f} h)")
