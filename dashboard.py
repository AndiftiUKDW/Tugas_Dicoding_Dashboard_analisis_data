import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from babel.numbers import format_currency

def create_order_bulanan(df):
    order_bulanan_df = df.resample(rule='M', on='order_approved_at').agg({
    "order_id" : "nunique",
    "payment_value":"sum"
    })
    order_bulanan_df.index = order_bulanan_df.index.strftime('%Y-%m')
    order_bulanan_df = order_bulanan_df.reset_index()
    order_bulanan_df = order_bulanan_df.rename(columns={
        'order_id' : "order_count"
    })
    return order_bulanan_df

def create_category(df):
    category_df = df.groupby(by="product_category_name_english").order_id.nunique().sort_values(ascending=False).reset_index()
    category_df = category_df.rename(columns={
        'order_id' : "count"
    })
    return category_df

def create_state(df):
    Brazil_data_df = df.groupby(by="customer_state").customer_id.nunique().sort_values(ascending=False).reset_index()
    Brazil_data_df = Brazil_data_df.rename(columns={'customer_id': 'value',
    'customer_state' : 'state_code'
    })
    Brazil = gpd.read_file('./braz/gadm41_BRA_1.shp')
    Brazil['state_code'] = Brazil['HASC_1'].str.replace('BR.','')
    merged = Brazil.merge(Brazil_data_df, left_on='state_code', right_on='state_code')
    return merged

def create_rfm(df,end):
    rfm_df = df.groupby(by='customer_id', as_index=False).agg({
        "order_approved_at":"max",
        "order_id":"nunique",
        "price": "sum"
    })
    rfm_df["recentcy"] = rfm_df['order_approved_at'].apply(lambda x: (end-x).days)
    rfm_df["index"] = range(1, len(rfm_df)+1)
    rfm_df.drop("order_approved_at",axis=1,inplace=True)
    rfm_df.columns = ["customer_id","frequency","monetary","recentcy" ,"index"]
    return rfm_df



customers_df = pd.read_csv("./Dataset/customers_dataset.csv")
order_items_df = pd.read_csv("./Dataset/order_items_dataset.csv")
order_payments_df = pd.read_csv("./Dataset/order_payments_dataset.csv")
order_reviews_df = pd.read_csv("./Dataset/order_reviews_dataset.csv")
orders_df = pd.read_csv("./Dataset/orders_dataset.csv")
products_df = pd.read_csv("./Dataset/products_dataset.csv")
translate_df = pd.read_csv("./Dataset/product_category_name_translation.csv")
sellers_df = pd.read_csv("./Dataset/sellers_dataset.csv")
order_items_df["shipping_limit_date"] = pd.to_datetime(order_items_df["shipping_limit_date"])
kolom = ["order_approved_at","order_purchase_timestamp","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"]
for isi in kolom:
    orders_df[isi] = pd.to_datetime(orders_df[isi])
product_translated_df = pd.merge(
    left = products_df,
    right = translate_df,
    how = "left",
    left_on = "product_category_name",
    right_on = "product_category_name"
)
all_order_df = pd.merge(
    left=orders_df,
    right=order_payments_df,
    how="left",
    left_on="order_id",
    right_on="order_id",
)
all_order_df = pd.merge(
    left=all_order_df,
    right=order_items_df,
    how="left",
    left_on="order_id",
    right_on="order_id",
)
all_order_df = pd.merge(
    left=all_order_df,
    right=order_reviews_df,
    how="left",
    left_on="order_id",
    right_on="order_id",
)
order_product_df = pd.merge(
    left=all_order_df,
    right=product_translated_df,
    how="left",
    left_on="product_id",
    right_on="product_id",
)
all_df = pd.merge(left=order_product_df,
    right=customers_df,
    how="left",
    left_on="customer_id",
    right_on="customer_id",
    )



columns = ["order_purchase_timestamp","order_approved_at","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date","shipping_limit_date"]
for column in columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date=all_df['order_approved_at'].min()
max_date=all_df['order_approved_at'].max()

with st.sidebar:
    st.image("https://s3-us-west-2.amazonaws.com/cbi-image-service-prd/original/4b74afb1-5a08-411d-a791-5cee8af6be67.png")
    start_date, end_date = st.date_input(
        label='Time Frame', min_value=min_date, max_value=max_date,
        value=[min_date,max_date]
    )

main_df = all_df[(all_df["order_approved_at"] >= str(start_date))&(all_df["order_approved_at"]<= str(end_date))]
bulanan_df = create_order_bulanan(main_df)
category_df = create_category(main_df)
brazil_df = create_state(main_df)
rfm_df = create_rfm(main_df,pd.to_datetime(end_date))

st.header("Brazil E-Commerce (Olist Store) Dashboard")
st.subheader("Monthly Order")
col1, col2 =st.columns(2)
with col1:
    total = bulanan_df.order_count.sum()
    st.metric("Total Order", value=total)

with col2:
    total_rev = bulanan_df.payment_value.sum()
    total_rev = format_currency(total_rev,'BRL',locale='pt_BR')
    st.metric("Total Revenue", value=total_rev)

fig, ax = plt.subplots(figsize=(16,8))
ax.plot(
    bulanan_df['order_approved_at'],
    bulanan_df['order_count'],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15, rotation=45)
st.pyplot(fig)

st.subheader("Best & Worst Performing Categories")
fig, ax = plt.subplots(nrows=1,ncols=2,figsize=(30,20))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(x="count", y="product_category_name_english", data=category_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel('number of sales', fontsize=30)
ax[0].set_title("Best Category", loc="center", fontsize=40)
ax[0].tick_params(axis ='y', labelsize=15, rotation=48)
ax[0].tick_params(axis ='x', labelsize=20)
 
sns.barplot(x="count", y="product_category_name_english", data=category_df.sort_values(by="count", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("number of sales",fontsize=30)
ax[1].invert_xaxis()
ax[1].set_title("Worst Category", loc="center", fontsize=40)
ax[1].yaxis.set_label_position("right")
ax[1].tick_params(axis ='y', labelsize=15,rotation=48)
ax[1].tick_params(axis ='x', labelsize=25)
st.pyplot(fig)

st.subheader("Most active online purchase by State")
colom1, colom2 = st.columns(2)
with colom1:
    st.write("Most Active")
    highest = brazil_df.sort_values(by="value",ascending=False).head(1)
    name = highest['NAME_1'].iloc[0]
    value = highest['value'].iloc[0]
    st.metric(name, value=value)
with colom2:
    st.write("Least Active")
    highest = brazil_df.sort_values(by="value").head(1)
    name = highest['NAME_1'].iloc[0]
    value = highest['value'].iloc[0]
    st.metric(name, value=value)
fig, ax = plt.subplots(figsize=(12, 10))
brazil_df.plot(column = 'value',cmap='OrRd',legend=True, figsize=(10,10),legend_kwds={'label': "Usage based on region", 'orientation': "horizontal"},ax=ax)
ax.set_title("Online E-Commerage usage")
st.pyplot(fig)

st.subheader("Best Customer Based on RFM")
col1, col2, col3 = st.columns(3)
with col1:
    avg_recen = round(rfm_df.recentcy.mean(),1)
    st.metric("Average Recency in days", value=avg_recen)
with col2:
    avg_freq = round(rfm_df.frequency.mean(),1)
    st.metric("Average Frequency", value=avg_freq)
with col3:
    avg_mon = round(rfm_df.monetary.mean(),1)
    avg_mon = format_currency(avg_mon,'BRL',locale='pt_BR')
    st.metric("Average Monetary", value=avg_mon)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]
sns.barplot(y="recentcy", x="index", data=rfm_df.sort_values(by="recentcy", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis ='x', labelsize=25)
ax[0].tick_params(axis='y', labelsize=30)
sns.barplot(y="frequency", x="index", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis ='x', labelsize=25)
ax[1].tick_params(axis='y', labelsize=30)
sns.barplot(y="monetary", x="index", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer", fontsize=30)
ax[2].set_title("By Spending", loc="center", fontsize=50)
ax[2].tick_params(axis ='x', labelsize=25)
ax[2].tick_params(axis='y', labelsize=30)
st.pyplot(fig)