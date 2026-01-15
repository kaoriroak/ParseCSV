import streamlit as st
import pandas as pd
import io

# 画面の設定
st.set_page_config(page_title="住所・電話番号変換ツール", layout="centered")

# --- メイン機能 ---
st.title("📦 住所・電話番号変換ツール")
st.info("CSVをアップロードすると、指定品番の抽出と、住所・電話番号の整形を自動で行います。")

# 抽出対象の品番（SKU管理番号）
TARGET_SKUS = [
    'mod2', 'mod3', 'mod4', 'ca-10', 'z-01', 'z-03', 
    'lb-4', 'kr--2', 'kr-03', 'bkye-c001', 'bkye-c002'
]

uploaded_file = st.file_uploader("CSVファイルを選択してください", type='csv')

if uploaded_file:
    content = uploaded_file.read()
    df = None
    for enc in ['shift_jis', 'utf-8-sig', 'cp932']:
        try:
            # 郵便番号と電話番号の各パーツを文字列として読み込む（0落ち防止）
            df = pd.read_csv(
                io.BytesIO(content), 
                encoding=enc, 
                dtype={
                    '送付先郵便番号1': str, '送付先郵便番号2': str,
                    '送付先電話番号1': str, '送付先電話番号2': str, '送付先電話番号3': str
                }
            )
            break
        except:
            continue

    if df is not None:
        df['SKU管理番号'] = df['SKU管理番号'].astype(str).str.strip()
        df_filtered = df[df['SKU管理番号'].isin(TARGET_SKUS)].copy()

        if df_filtered.empty:
            st.warning("対象の品番（SKU）が見つかりませんでした。")
        else:
            processed_data = []
            for _, row in df_filtered.iterrows():
                # --- 郵便番号の整形 ---
                z1 = str(row.get('送付先郵便番号1', '')).strip().split('.')[0].zfill(3)
                z2 = str(row.get('送付先郵便番号2', '')).strip().split('.')[0].zfill(4)
                zip_code = f"〒{z1}-{z2}" if (z1 != 'nan' and z2 != 'nan' and z1 != '000') else ""

                # --- 住所の整形 ---
                pref = str(row.get('送付先住所都道府県', '')).replace('nan', '')
                city = str(row.get('送付先住所郡市区', '')).replace('nan', '')
                addr1 = (pref + city).strip()
                addr2 = str(row.get('送付先住所それ以降の住所', '')).replace('nan', '').strip()

                # --- 電話番号の整形（1-2-3をハイフンで結合） ---
                t1 = str(row.get('送付先電話番号1', '')).strip().split('.')[0].replace('nan', '')
                t2 = str(row.get('送付先電話番号2', '')).strip().split('.')[0].replace('nan', '')
                t3 = str(row.get('送付先電話番号3', '')).strip().split('.')[0].replace('nan', '')
                
                if t1 and t2 and t3:
                    phone_number = f"{t1}-{t2}-{t3}"
                else:
                    phone_number = (t1 + t2 + t3).strip()

                # --- 宛名の整形 ---
                ln = str(row.get('送付先姓', '')).replace('nan', '').strip()
                fn = str(row.get('送付先名', '')).replace('nan', '').strip()
                name = f"{ln} {fn} 様" if (ln and fn) else f"{ln}{fn} 様"

                processed_data.append([zip_code, addr1, addr2, phone_number, name])

            # 結果の表示とダウンロード
            result_df = pd.DataFrame(processed_data, columns=["郵便番号", "住所1", "住所2", "
