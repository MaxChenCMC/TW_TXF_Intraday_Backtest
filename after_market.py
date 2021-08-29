import streamlit as st
import pandas as pd
import requests, time, datetime  # Pep8 request inline coment upper its first letter.__#_井前空2後空1。說不同套件不該擠在同一行，而只引用一個大套件的其中數個小套件就可擠同一行
from io import StringIO
from bs4 import BeautifulSoup
from FinMind.data import DataLoader

market_closed = 5
last_update = pd.read_html("https://www.taifex.com.tw/cht/3/futContractsDate")[2].loc[
    0, 0
][-10:]
date_format = pd.date_range(
    end=pd.to_datetime(last_update), periods=5 + market_closed, freq="B"
)
date_df = date_format.strftime("%Y-%m-%d")
date_tse = date_format.strftime("%Y%m%d")
date_txf = date_format.strftime("%Y/%m/%d")


def oi_last():
    df = pd.read_html("https://www.taifex.com.tw/cht/3/futContractsDate")[3][3:15]
    df = df[(df[0] == "序號") | (df[1] == "臺股期貨") | (df[1] == "小型臺指期貨")]
    df = df[[1, 2, 7, 13]]
    df.columns = ["商品名稱", "身份別", "多空淨額(口數)", "未平倉餘額(口數)"]
    df.set_index("商品名稱", inplace=True)
    df.index.name = ""
    return df


def oi_history():
    tb = []
    for i in range(len(date_format)):
        r = requests.get(
            "https://www.twse.com.tw/fund/BFI82U?response=csv&dayDate="
            + date_tse[i]
            + "&type=day"
        )
        if r.text != "\r\n":
            df = (
                pd.read_csv(StringIO(r.text), header=1)
                .dropna(how="all", axis=1)
                .dropna(how="any")
            )
            institution = int(df.loc[3, "買賣差額"].replace(",", ""))  # 外資及陸資(不含自營)
            trust = int(df.loc[2, "買賣差額"].replace(",", ""))  # 投信
            time.sleep(3)
            # 現貨沒休市的話 期貨也不必偵錯了 直接爬
            myobj = {"queryDate": date_txf[i], "queryType": 1}
            response = requests.post(
                "https://www.taifex.com.tw/cht/3/futContractsDate", data=myobj
            )
            soup = BeautifulSoup(response.text, features="html.parser")
            table = soup.find("table", class_="table_f")
            tx = table.find_all("tr")[5].find_all("td")
            txnet = int([i.text.strip() for i in tx][4].replace(",", ""))
            txoi = int([i.text.strip() for i in tx][10].replace(",", ""))
            mtx = table.find_all("tr")[14].find_all("td")
            mtxnet = int([i.text.strip() for i in mtx][4].replace(",", ""))
            mtxoi = int([i.text.strip() for i in mtx][10].replace(",", ""))
            res = [date_df[i], institution, trust, txnet, txoi, mtxnet, mtxoi]
            tb.append(res)
        else:
            print(f"{date_df[i]}休市\n")


def oi_history():
    tb = []
    for i in range(len(date_format)):
        r = requests.get(
            "https://www.twse.com.tw/fund/BFI82U?response=csv&dayDate="
            + date_tse[i]
            + "&type=day"
        )
        if r.text != "\r\n":
            df = (
                pd.read_csv(StringIO(r.text), header=1)
                .dropna(how="all", axis=1)
                .dropna(how="any")
            )
            institution = int(df.loc[3, "買賣差額"].replace(",", ""))  # 外資及陸資(不含自營)
            trust = int(df.loc[2, "買賣差額"].replace(",", ""))  # 投信
            time.sleep(3)
            # 現貨沒休市的話 期貨也不必偵錯了 直接爬
            myobj = {"queryDate": date_txf[i], "queryType": 1}
            response = requests.post(
                "https://www.taifex.com.tw/cht/3/futContractsDate", data=myobj
            )
            soup = BeautifulSoup(response.text, features="html.parser")
            table = soup.find("table", class_="table_f")
            tx = table.find_all("tr")[5].find_all("td")
            txnet = int([i.text.strip() for i in tx][4].replace(",", ""))
            txoi = int([i.text.strip() for i in tx][10].replace(",", ""))
            mtx = table.find_all("tr")[14].find_all("td")
            mtxnet = int([i.text.strip() for i in mtx][4].replace(",", ""))
            mtxoi = int([i.text.strip() for i in mtx][10].replace(",", ""))
            res = [date_df[i], institution, trust, txnet, txoi, mtxnet, mtxoi]
            tb.append(res)
        else:
            print(f"{date_df[i]}休市\n")

    oi = pd.DataFrame(
        data=tb,
        columns=[
            "date",
            "inst_f buy",
            "inst_t buy",
            "inst_txf_net",
            "inst_txf_oi",
            "inst_mtx_net",
            "inst_mtx_oi",
        ],
    )
    oi["date"] = pd.to_datetime(oi["date"])
    oi.set_index("date", inplace=True)
    global oi_index
    oi_index = oi.index
    return oi


def gold_ma():
    fm = DataLoader()
    tse50 = pd.read_html("https://www.taifex.com.tw/cht/9/futuresQADetail")[0]["證券名稱"][
        :50
    ].to_list()
    start = (
        pd.to_datetime(date_df[0]) - datetime.timedelta(days=14 + market_closed)
    ).strftime("%Y-%m-%d")
    tw50_df = pd.DataFrame(
        {i: fm.taiwan_stock_daily(i, start, date_df[-1])["close"] for i in tse50}
    )
    tw50 = tw50_df > tw50_df.rolling(10).mean()
    tw50 = tw50.sum(axis=1)[-5 - market_closed :]
    tw50.index = oi_index
    return tw50


def active():
    st.subheader(f"{last_update}三大法人大小台動向")
    st.text("盤後15:00左右更新")
    st.table(oi_last())

    st.header("歷史行情籌碼解讀")
    show = st.button("我瞧瞧(需要2分鐘)")
    if show:
        comb = pd.concat([oi_history(), gold_ma()], axis=1)
        comb.index = comb.index.strftime("%Y-%m-%d")
        comb.columns = [
            "外資現股買賣超",
            "投信現股買賣超",
            "外資大台多空淨額",
            "外資大台未平倉",
            "外資小台多空淨額",
            "外資小台未平倉",
            "前50大權值股站上十日線總檔數",
        ]
        st.table(comb.tail())
        st.markdown(
            """
        ● 法人現股買賣超若比過去5日的平均值還多，表示法人偏多；反之則偏空。

        ● 外資大小台當日多空淨額若為正，即表示偏多，而未平倉口數若較過去5日的中位數高，即表示行情偏多；反之則偏空。

        ● 上市前50大權值股中，若站上十日線的檔數比過去5日平均還多，則行情偏多。

        `歷史行情7個欄位中，若都沒出現訊號則行情偏空，而訊號 4~7 則行情偏多`

        """
        )
        df = pd.DataFrame()
        df["f1"] = (
            comb.iloc[:, 0] > comb.iloc[:, 0].rolling(5).mean()
        )  # 中位 ☛ 多停85；空整體都有利
        df["f2"] = comb.iloc[:, 1] > comb.iloc[:, 1].rolling(5).mean()  # 唯一選擇 平均
        df["f3"] = comb.iloc[:, 2] > 0
        df["f4"] = comb.iloc[:, 3] > comb.iloc[:, 3].rolling(5).median()
        df["f5"] = comb.iloc[:, 4] > 0
        df["f6"] = (comb.iloc[:, 5] > comb.iloc[:, 5].rolling(5).median()) & (
            comb.iloc[:, 5] > 0
        )
        df["f7"] = comb.iloc[:, 6] > comb.iloc[:, 6].rolling(5).mean()
        df.columns = [
            "外資現股買賣超",
            "投信現股買賣超",
            "外資大台多空淨額",
            "外資大台未平倉",
            "外資小台多空淨額",
            "外資小台未平倉",
            "前50大權值股站上十日線總檔數",
        ]
        st.table(df.tail(1))
        df_ = df.sum(axis=1).to_frame().tail().T
        df_.index = ["訊號"]
        st.table(df_)


active()
