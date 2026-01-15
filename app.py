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
            # 読み込み時に全パーツを「str（文字列）」に指定して0落ちを物理的に防ぐ
            df = pd.read_csv(
                io.BytesIO(content), 
                encoding=enc, 
                dtype={
                    '送付先郵便番号1': str, 
                    '送付先郵便番号2': str,
                    '送付先電話番号1': str, 
                    '送付先電話番号2': str, 
                    '送付先電話番号3': str,
                    'SKU管理番号': str
                }
            )
            break
        except:
            continue

    if df is not None:
        # SKUの前後空白を削除
        df['SKU管理番号'] = df['SKU管理番号'].fillna('').str.strip()
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

                # --- 電話番号の整形（0落ち対策を強化） ---
                def format_phone_part(val):
                    s = str(val).strip().split('.')[0].replace('nan', '')
                    return s

                t1 = format_phone_part(row.get('送付先電話番号1', ''))
                t2 = format_phone_part(row.get('送付先電話番号2', ''))
                t3 = format_phone_part(row.get('送付先電話番号3', ''))
                
                # 電話番号1の先頭が0で始まっておらず、かつ空でない場合、0を補完する（090が90になっているケース等）
                if t1 and not t1.startswith('0'):
                    t1 = '0' + t1

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
            result_df = pd.DataFrame(processed_data, columns=["郵便番号", "住所1", "住所2", "電話番号", "宛名"])
            st.success(f"{len(result_df)}件のデータを抽出・整形しました。")
            st.dataframe(result_df)

            # CSV出力時も0が消えないように設定
            csv_output = result_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="変換済みCSVをダウンロード",
                data=csv_output,
                file_name="converted_shipping_list.csv",
                mime="text/csv"
            )
    else:
        st.error("ファイルの読み込みに失敗しました。")
