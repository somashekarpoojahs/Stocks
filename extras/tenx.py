# 10x screen: move needed at Friday 23 Oct expiry for the option to be worth 10x its ask.
# Columns: implied = options-implied earnings move, avg = historical average earnings move
rows = [
 # sym, earnings, spot, type, strike, bid, ask, delta, OI, implied%, avg%, tech
 ("NFLX","Tue 20 Oct after close",69.28,"P",60,0.40,0.41,-0.097,10061,9.4,10.2,"BEARISH"),
 ("NFLX","Tue 20 Oct after close",69.28,"P",58,0.21,0.22,-0.058,2277,9.4,10.2,"BEARISH"),
 ("NFLX","Tue 20 Oct after close",69.28,"C",80,0.42,0.44,0.115,12579,9.4,10.2,"BEARISH"),
 ("NFLX","Tue 20 Oct after close",69.28,"C",82,0.26,0.28,0.079,3825,9.4,10.2,"BEARISH"),
 ("META","Wed 21 Oct after close",691.12,"C",770,3.30,3.50,0.116,1554,7.1,10.4,"NO TRADE"),
 ("META","Wed 21 Oct after close",691.12,"C",790,1.71,1.84,0.067,5832,7.1,10.4,"NO TRADE"),
 ("META","Wed 21 Oct after close",691.12,"P",620,3.40,3.70,-0.112,1337,7.1,10.4,"NO TRADE"),
 ("META","Wed 21 Oct after close",691.12,"P",600,1.67,1.72,-0.060,3657,7.1,10.4,"NO TRADE"),
 ("TSLA","Wed 21 Oct after close",374.53,"C",410,2.22,2.25,0.145,8452,7.3,9.6,"NO TRADE"),
 ("TSLA","Wed 21 Oct after close",374.53,"C",420,1.26,1.28,0.089,8936,7.3,9.6,"NO TRADE"),
 ("TSLA","Wed 21 Oct after close",374.53,"P",340,1.72,1.74,-0.114,3899,7.3,9.6,"NO TRADE"),
 ("TSLA","Wed 21 Oct after close",374.53,"P",330,0.81,0.82,-0.059,3498,7.3,9.6,"NO TRADE"),
 ("BE","Thu 22 Oct after close",223.11,"P",185,1.26,1.31,-0.083,678,12.4,16.5,"BEARISH"),
 ("BE","Thu 22 Oct after close",223.11,"P",175,0.49,0.66,-0.041,1686,12.4,16.5,"BEARISH"),
 ("SPOT","Thu 22 Oct before open",527.56,"C",590,4.20,5.20,0.171,152,9.4,11.7,"BULLISH"),
 ("SPOT","Thu 22 Oct before open",527.56,"C",610,2.22,3.15,None,18,9.4,11.7,"BULLISH"),
 ("WDC","Thu 22 Oct after close",363.66,"P",320,2.35,2.61,-0.120,427,10.3,9.4,"BEARISH"),
 ("WDC","Thu 22 Oct after close",363.66,"P",300,0.77,0.98,-0.047,762,10.3,9.4,"BEARISH"),
]
out=[]
for s,e,S,t,K,b,a,d,oi,imp,avg,tech in rows:
    lvl = K+10*a if t=="C" else K-10*a
    need = (lvl/S-1)*100
    sprd = (a-b)/a*100
    aligned = (t=="P" and tech=="BEARISH") or (t=="C" and tech=="BULLISH")
    out.append((abs(need)/avg, s,e,t,K,a*100,need,imp,avg,abs(d) if d else None,oi,sprd,tech,aligned))
out.sort()
print(f"{'#':>2} {'SYM':4} {'OPT':6} {'COST':>5} {'10x needs':>9} {'impl':>5} {'avg':>5} {'x avg':>5} {'ITM~':>5} {'OI':>6} {'sprd%':>5}  TECH")
for i,(r,s,e,t,K,cost,need,imp,avg,d,oi,sp,tech,al) in enumerate(out,1):
    dd=f"{d*100:.0f}%" if d else "  -"
    print(f"{i:>2} {s:4} {K}{t:<3} ${cost:>4.0f} {need:+8.1f}% {imp:5.1f} {avg:5.1f} {r:5.2f} {dd:>5} {oi:>6} {sp:5.0f}  {tech}{' (aligned)' if al else ''}")
