from pathlib import Path
import pandas as pd, streamlit as st, plotly.express as px
from src.greenops import GreenOpsDetector, deduplicate_invoices
ROOT=Path(__file__).parent
st.set_page_config(page_title="GreenOps AI",page_icon="🌱",layout="wide")
st.title("🌱 GreenOps AI")
st.caption("Sustainability monitoring and anomaly detection | Synthetic demonstration data")
@st.cache_data
def load():
 return pd.read_csv(ROOT/"data/facility_readings_400k.csv.gz", compression="gzip"),pd.read_csv(ROOT/"data/monthly_invoices.csv")
@st.cache_resource
def train(sample, meter_reference):
 detector=GreenOpsDetector(contamination=.03)
 detector.fit(sample, meter_reference=meter_reference)
 return detector
df,inv=load()
st.warning("All facility and invoice records are synthetic. This ESG/BRSR data-auditing prototype is for decision support only—not production software, SEBI certification, legal advice, or an automated disclosure/payment system.")
clean,dups=deduplicate_invoices(inv)
a,b,c,d=st.columns(4)
a.metric("Reading records",f"{len(df):,}"); b.metric("Sites",df.site_id.nunique())
c.metric("Duplicate invoice rows",len(dups)); d.metric("Missing diesel logs",int(((df.resource_type=="diesel")&(~df.generator_log_present)).sum()))
t1,t2,t3,t4=st.tabs(["Overview","ML anomaly review","Invoice controls","Data quality"])
with t1:
 x,y=st.columns(2)
 monthly=df.assign(month=pd.to_datetime(df.timestamp).dt.to_period("M").astype(str)).groupby(["month","resource_type"],as_index=False).consumption.sum()
 x.plotly_chart(px.line(monthly,x="month",y="consumption",color="resource_type",title="Monthly resource consumption"),use_container_width=True)
 em=df.groupby("site_id",as_index=False).emissions_kgco2e.sum().sort_values("emissions_kgco2e",ascending=False)
 y.plotly_chart(px.bar(em,x="site_id",y="emissions_kgco2e",title="Estimated emissions by site"),use_container_width=True)
 st.caption("Emission factors are illustrative and must be replaced by approved organizational factors.")
with t2:
 st.write("Train an Isolation Forest on a reproducible sample, then score unseen rows. Explicit rules add operational explanations.")
 training=df.sample(min(30000,len(df)),random_state=11).copy()
 detector=train(training, df)
 sample=df.drop(training.index).sample(min(250,len(df)-len(training)),random_state=42).copy()
 duplicate_ids=set(dups.invoice_id.astype(str))
 output=[]
 for _,r in sample.iterrows():
  item=r.to_dict()
  item["duplicate_invoice_flag"]=str(r.invoice_id) in duplicate_ids
  output.append({**{k:item.get(k) for k in ["timestamp","site_id","meter_id","resource_type","consumption"]},**detector.predict_one(item)})
 results=pd.DataFrame(output)
 flagged=results[results.flagged].sort_values("anomaly_score")
 st.metric("Flagged rows in unseen sample",len(flagged))
 st.dataframe(flagged.head(100),use_container_width=True)
 st.caption("Synthetic labels are not used for model training or inference. Meter changes are inferred by comparing observed meter IDs with the learned site/resource baseline. Review every alert against source evidence before action.")
with t3:
 st.metric("Invoice rows",len(inv)); st.metric("Unique invoice IDs",len(clean)); st.metric("Rows in duplicate exception queue",len(dups))
 st.dataframe(dups.head(100),use_container_width=True)
with t4:
 q=pd.DataFrame({"Check":["Missing diesel logs","Changed meter IDs","Duplicate invoice rows"],"Count":[int(((df.resource_type=="diesel")&(~df.generator_log_present)).sum()),int(df.meter_id_changed_flag.sum()),len(dups)]})
 st.dataframe(q,use_container_width=True)
 st.write("Retain source records, reconcile meter master data, and require finance/site-owner approval before payment or reporting.")
