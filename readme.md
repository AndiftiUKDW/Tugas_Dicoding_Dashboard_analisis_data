Untuk menjalankan Streamlit pada local perlu melakukan command berikut ini agar membuat environment terlebih dahulu pada cmd
```
python3 -m venv myenv
.\myenv\Scripts\activate
```
Kemudian menginstall package yang diperlukan
```
pip install pandas
pip install geopandas
pip install matplotlib
pip install streamlit
pip install seaborn
pip install babel
```
Lalu menjalankan streamlit dashboard dengan cara ini
```
streamlit run dashboard.py
```