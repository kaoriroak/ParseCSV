import streamlit as st
import pandas as pd
import io

# 画面の設定
st.set_page_config(page_title="住所データ変換アプリ", layout="centered")

st.title("📦 住所データ変換ツール")
st.write("CSVをアップロードすると、指定の品番のみを抽出し、配送用フォーマットに変換します。")

# 抽出対象の品番（SKU管理番号）
TARGET_SKUS = [
    'mod2', 'mod3', 'mod4', 'ca-10', 'z-01', 'z-03', 
    'lb-4', 'kr--2', 'kr-03', 'bkye-c001', 'bkye-c002'
]

# ファイル選択
uploaded_file = st.file_uploader("CSVファイルを選択してください", type='csv')

if uploaded_file:
    # 文字コード対応
    content = uploaded_file.read()
    df = None
    for enc in ['shift_jis', 'utf-8-sig', 'cp932']:
        try:
            df = pd.read_csv(io.BytesIO(content), encoding=enc, dtype={'送付先郵便番号1': str, '送付先郵便番号2': str})
            break
        except:
            continue

    if df is not None:
        # SKUフィルタリング
        df['SKU管理番号'] = df['SKU管理番号'].astype(str).str.strip()
        df_filtered = df[df['SKU管理番号'].isin(TARGET_SKUS)].copy()

        if df_filtered.empty:
            st.warning("対象の品番（SKU）が見つかりませんでした。")
        else:
            processed_data = []
            for _, row in df_filtered.iterrows():
                # 郵便番号（0埋め対応）
                z1 = str(row.get('送付先郵便番号1', '')).strip().split('.')[0].zfill(3)
                z2 = str(row.get('送付先郵便番号2', '')).strip().split('.')[0].zfill(4)
                zip_code = f"〒{z1}-{z2}" if (z1 != '000' and z2 != '0000') else ""

                # 住所
                pref = str(row.get('送付先住所都道府県', '')).replace('nan', '')
                city = str(row.get('送付先住所郡市区', '')).replace('nan', '')
                addr1 = (pref + city).strip()
                addr2 = str(row.get('送付先住所それ以降の住所', '')).replace('nan', '').strip()

                # 宛名
                ln = str(row.get('送付先姓', '')).replace('nan', '').strip()
                fn = str(row.get('送付先名', '')).replace('nan', '').strip()
                name = f"{ln} {fn} 様" if (ln and fn) else "データ確認が必要"

                processed_data.append([zip_code, addr1, addr2, name])

            # 結果表示
            result_df = pd.DataFrame(processed_data, columns=["郵便番号", "住所1", "住所2", "宛名"])
            st.success(f"{len(result_df)}件のデータを抽出しました。")
            st.dataframe(result_df)

            # ダウンロード
            csv_output = result_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="変換済みCSVをダウンロード",
                data=csv_output,
                file_name="converted_list.csv",
                mime="text/csv"
            )
    else:
        st.error("ファイルの読み込みに失敗しました。")