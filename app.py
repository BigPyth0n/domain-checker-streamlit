import streamlit as st
import random
import whois
import json
import datetime
import os
from typing import List, Tuple
import pandas as pd

# --- توابع مربوط به بارگذاری و ذخیره لیست کلمات ---


def save_words_to_json(word_list: List[str], filename: str):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(word_list, f, indent=4, ensure_ascii=False)
        st.sidebar.success(
            f"Successfully saved {len(word_list)} words to {filename}.")
    except Exception as e:
        st.sidebar.error(f"Error saving to {filename}: {str(e)}")


def load_words_from_json(filename: str) -> List[str]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# تابع برای بارگذاری لیست‌های کلمات منتخب


def load_curated_list(filename: str) -> List[str]:
    words = load_words_from_json(filename)
    if not words:
        st.sidebar.warning(f"فایل '{filename}' یافت نشد یا خالی است.")
    return words


# --- دیکشنری پسوندها و قیمت‌ها ---
domain_extensions_data = {
    1: (".nl", "6897290"), 2: (".info", "4927230"), 3: (".xyz", "3605402"),
    4: (".in", "13264020"), 5: (".at", "12130549"), 6: (".online", "3557169"),
    7: (".me", "10699054"), 8: (".vip", "16929713"), 9: (".live", "4039497"),
    10: (".trade", "6692301"), 11: (".cc", "9960073"), 12: (".ir", "450000"),
    13: (".mobi", "7114338"), 14: (".express", "13505184"), 15: (".io", "46725525"),
    16: (".icu", "4482844"), 17: (".work", "10418285"), 18: (".zone", "13505184"),
    19: (".site", "2351349"), 20: (".life", "3014550"), 21: (".space", "2351349"),
    22: (".club", "16929713"), 23: (".ltd", "8983359"), 24: (".link", "9067766"),
    25: (".works", "9887724"), 26: (".pro", "4721929"), 27: (".asia", "14325142"),
    28: (".app", "19244887"), 29: (".rocks", "5064444"), 30: (".tech", "4762989"),
    31: (".plus", "13505184"), 32: (".cloud", "18666094"), 33: (".biz", "20836570"),
    34: (".dev", "16495618"), 35: (".observer", "11394999"),
    37: (".direct", "18027009"), 38: (".store", "3557169"), 39: (".solutions", "9887724"),
    40: (".shop", "2399582"), 47: (".website", "2351349"), 48: (".today", "4039497"),
    49: (".name", "8296042"), 50: (".guru", "4039497"), 51: (".show", "16218279"),
    52: (".london", "36488113"), 53: (".design", "50933837"), 55: (".center", "10792089"),
    56: (".news", "13505184"), 57: (".tel", "11202068"), 58: (".win", "6692301"),
    59: (".email", "6089391"), 60: (".company", "8139285"), 61: (".systems", "24357564"),
    62: (".li", "8513089"), 63: (".host", "97671420"), 64: (".one", "17303517"),
    65: (".loan", "6692301"), 66: (".business", "4039497"), 67: (".world", "3014550"),
    68: (".click", "2399582"), 70: (".ink", "26045712"), 71: (".market", "40768774"),
    72: (".tv", "31110156"), 73: (".bid", "6692301"), 74: (".stream", "6692301"),
    76: (".men", "6692301"), 77: (".pw", "7174629"), 78: (".photography", "13505184"),
    79: (".exchange", "13505184"), 81: (".ph", "54985392"), 82: (".buzz", "33642378"),
    83: (".international", "13505184"), 84: (".media", "8139285"),
    86: (".berlin", "55720942"), 87: (".jobs", "198960300"), 90: (".group", "9887724"),
    91: (".global", "36114309"), 92: (".art", "3574321"), 93: (".blog", "4762989"),
    94: (".studio", "19835739"), 95: (".ooo", "27480638"), 97: (".digital", "3014550"),
    98: (".services", "10792089"), 99: (".expert", "10792089"), 100: (".tools", "16218279"),
    101: (".agency", "8139285"),
    102: (".network", "8139285")
}
temp_extensions = {}
seen_tlds = set()
for key, (tld, price_val) in domain_extensions_data.items():
    if tld not in seen_tlds:
        temp_extensions[key] = (tld, price_val)
        seen_tlds.add(tld)
domain_extensions = temp_extensions


# --- توابع کاربردی ---
def price_to_number(price: str) -> float:
    price_clean = price.replace(",", "").strip()
    try:
        return float(price_clean)
    except ValueError:
        return float('inf')


def generate_random_words(count: int, length: int) -> List[str]:
    letters = "abcdefghijklmnopqrstuvwxyz"
    words = set()
    if count == 0:
        return []
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    for i in range(count * 2):
        word = ''.join(random.choice(letters) for _ in range(length))
        words.add(word)
        progress = min((i + 1) / (count * 1.5), 1.0)
        progress_bar.progress(progress)
        status_text.text(
            f"تولید کلمه تصادفی {length} حرفی: {len(words)}/{count}")
        if len(words) >= count:
            break
    progress_bar.empty()
    status_text.empty()
    return list(words)[:count]


def check_domain_availability(domain: str) -> str:
    try:
        w = whois.whois(domain)
        if w is None or not hasattr(w, 'status'):
            return "Available"
        if w.status is None or \
           (isinstance(w.status, list) and any("available" in str(s).lower() for s in w.status)) or \
           (isinstance(w.status, str) and "available" in w.status.lower()) or \
           (hasattr(w, 'text') and ("no match" in str(w.text).lower() or "not found" in str(w.text).lower())) or \
           (hasattr(w, 'registrar') and w.registrar is None and w.creation_date is None) or \
           w.expiration_date is None or \
           (isinstance(w.expiration_date, list) and not w.expiration_date):
            return "Available"
        else:
            return "Registered"
    except whois.parser.PywhoisError as e:
        if "no match for" in str(e).lower() or "no entries found" in str(e).lower():
            return "Available"
        return f"Error: WHOIS Lookup ({str(e)})"
    except Exception as e:
        common_errors = ["no whois server", "no match", "not found",
                         "failed to connect", "timed out", "network is unreachable"]
        if any(err_msg in str(e).lower() for err_msg in common_errors):
            return "Available"
        return f"Error: General ({str(e)})"


def save_results_to_json(domains_df: pd.DataFrame,
                         domain_extension: str,
                         price_val: str,
                         list_type_identifier: str) -> str:
    filename = f"available_domains_{list_type_identifier}_{domain_extension.replace('.', '_')}.json"

    available_domains = domains_df[domains_df["وضعیت"] == "Available"]
    if available_domains.empty:
        st.warning(
            f"هیچ دامنه آزاد جدیدی برای لیست '{list_type_identifier}' و پسوند '{domain_extension}' یافت نشد. فایل '{filename}' به‌روز نشد."
        )
        return filename

    try:
        with open(filename, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            existing_domain_names = {item["domain"] for item in existing_data}
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []
        existing_domain_names = set()

    new_domains_to_save = []
    for index, row in available_domains.iterrows():
        full_domain_name = row["دامنه کامل"]
        if full_domain_name not in existing_domain_names:
            new_domains_to_save.append({
                "domain": full_domain_name,
                "checked_at": datetime.datetime.now().isoformat(),
                "price": price_val
            })

    if new_domains_to_save:
        all_data = existing_data + new_domains_to_save
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4,
                      sort_keys=True, ensure_ascii=False)
        st.success(
            f"{len(new_domains_to_save)} دامنه آزاد جدید در فایل '{filename}' ذخیره شد. مجموعاً {len(all_data)} دامنه در فایل موجود است."
        )
    else:
        st.info(
            f"هیچ دامنه آزاد *جدیدی* برای ذخیره در لیست '{list_type_identifier}' با پسوند '{domain_extension}' یافت نشد. فایل '{filename}' بدون تغییر باقی ماند."
        )
    return filename


def main():
    st.set_page_config(layout="wide", page_title="ابزار بررسی دامنه")
    st.title("ابزار بررسی در دسترس بودن دامنه 🔎")

    st.sidebar.title("📚 تنظیمات لیست کلمات")
    word_source_options = {
        "تصادفی": "تولید کلمات تصادفی",
        "منتخب طولانی": "لیست منتخب (بیش از ۹۰۰ کلمه)",
        "منتخب ۵۰۰": "لیست منتخب خلاقانه (۵۰۰ کلمه)",
        # <-- گزینه جدید اضافه شد
        "منتخب ۱۰۰ خلاقانه": "لیست منتخب ۱۰۰ کلمه (ویژه)"
    }
    word_source_key = st.sidebar.radio(
        "منبع کلمات برای بررسی دامنه را انتخاب کنید:",
        options=list(word_source_options.keys()),
        format_func=lambda key: word_source_options[key],
        key="word_source_selector"  # Added key for uniqueness
    )

    words_to_check_from_source = []
    list_type_id_for_save = ""

    if word_source_key == "تصادفی":
        list_type_id_for_save = "random"
        st.sidebar.subheader("⚙️ تنظیمات تولید کلمات تصادفی")
        word_count_for_dict = st.sidebar.number_input(
            "تعداد کلمات برای هر دیکشنری تصادفی (مثلاً ۱۰۰):",
            min_value=0, value=10, step=10,
            key="random_word_count_dict"  # Added key
        )
        if word_count_for_dict > 0:
            if st.sidebar.button("تولید و ذخیره لیست‌های تصادفی جدید", key="gen_random_btn"):
                three_letter_words = generate_random_words(
                    word_count_for_dict, 3)
                four_letter_words = generate_random_words(
                    word_count_for_dict, 4)
                save_words_to_json(three_letter_words,
                                   "three_letter_words.json")
                save_words_to_json(four_letter_words, "four_letter_words.json")
            else:
                three_letter_words = load_words_from_json(
                    "three_letter_words.json")
                four_letter_words = load_words_from_json(
                    "four_letter_words.json")
                if not three_letter_words and not four_letter_words:
                    st.sidebar.caption(
                        "لیست‌های تصادفی موجود نیستند. برای تولید، دکمه بالا را بزنید.")
                else:
                    st.sidebar.caption(
                        f"بارگذاری شده: {len(three_letter_words)} کلمه ۳حرفی، {len(four_letter_words)} کلمه ۴حرفی")

    elif word_source_key == "منتخب طولانی":
        list_type_id_for_save = "curated_900_plus"
        words_to_check_from_source = load_curated_list(
            "curated_ai_trade_words.json")
        if words_to_check_from_source:
            st.sidebar.info(
                f"لیست منتخب (بیش از ۹۰۰ کلمه) شامل {len(words_to_check_from_source)} کلمه بارگذاری شد."
            )

    elif word_source_key == "منتخب ۵۰۰":
        list_type_id_for_save = "curated_500"
        words_to_check_from_source = load_curated_list(
            "curated_500_ai_trade_words.json")
        if words_to_check_from_source:
            st.sidebar.info(
                f"لیست منتخب خلاقانه (۵۰۰ کلمه) شامل {len(words_to_check_from_source)} کلمه بارگذاری شد."
            )

    elif word_source_key == "منتخب ۱۰۰ خلاقانه":  # <-- بلاک جدید برای لیست ۱۰۰ کلمه‌ای
        list_type_id_for_save = "curated_100_creative"
        words_to_check_from_source = load_curated_list(
            "curated_100_ai_trade_words.json")
        if words_to_check_from_source:
            st.sidebar.info(
                f"لیست منتخب ۱۰۰ کلمه (ویژه) شامل {len(words_to_check_from_source)} کلمه بارگذاری شد."
            )

    st.header("🌐 انتخاب پسوند دامنه")
    sort_option = st.selectbox("مرتب‌سازی پسوندها بر اساس قیمت:", [
                               "بدون مرتب‌سازی", "صعودی", "نزولی"], key="tld_sort_option")

    sorted_extensions_dict = domain_extensions.copy()
    if sort_option == "صعودی":
        sorted_extensions_dict = dict(
            sorted(domain_extensions.items(),
                   key=lambda item: price_to_number(item[1][1]))
        )
    elif sort_option == "نزولی":
        sorted_extensions_dict = dict(
            sorted(domain_extensions.items(),
                   key=lambda item: price_to_number(item[1][1]), reverse=True)
        )

    selectbox_options = list(sorted_extensions_dict.items())
    selected_key_id = st.selectbox(
        "یک پسوند دامنه انتخاب کنید:",
        options=[item[0] for item in selectbox_options],
        format_func=lambda key_id_func: f"{sorted_extensions_dict[key_id_func][0]} - قیمت: {sorted_extensions_dict[key_id_func][1]}",
        key="tld_selector"
    )
    domain_extension_val, price_val = sorted_extensions_dict[selected_key_id]

    if word_source_key == "تصادفی":
        st.header("🔢 تعداد دامنه‌ها برای بررسی (از لیست تصادفی)")
        three_letter_count_to_check = st.number_input(
            "تعداد دامنه‌های ۳ حرفی برای بررسی:", min_value=0, value=5, step=5, key="three_check_count"
        )
        four_letter_count_to_check = st.number_input(
            "تعداد دامنه‌های ۴ حرفی برای بررسی:", min_value=0, value=5, step=5, key="four_check_count"
        )

    if st.button("🚀 شروع بررسی دامنه‌ها", type="primary", use_container_width=True, key="start_check_button"):
        final_words_to_process = []

        if word_source_key == "تصادفی":
            three_loaded = load_words_from_json("three_letter_words.json")
            four_loaded = load_words_from_json("four_letter_words.json")
            if 'three_letter_count_to_check' in locals() and three_letter_count_to_check > 0 and three_loaded:
                final_words_to_process.extend(
                    random.sample(three_loaded, min(
                        three_letter_count_to_check, len(three_loaded)))
                )
            if 'four_letter_count_to_check' in locals() and four_letter_count_to_check > 0 and four_loaded:
                final_words_to_process.extend(
                    random.sample(four_loaded, min(
                        four_letter_count_to_check, len(four_loaded)))
                )

            # Check if counts were defined and if any words were added
            random_counts_defined = 'three_letter_count_to_check' in locals(
            ) and 'four_letter_count_to_check' in locals()
            if not final_words_to_process and random_counts_defined and (three_letter_count_to_check > 0 or four_letter_count_to_check > 0):
                st.warning(
                    "لیست کلمات تصادفی برای نمونه‌برداری خالی است یا هنوز تولید نشده. لطفاً ابتدا کلمات را تولید کنید.")
            elif not final_words_to_process and random_counts_defined:  # Counts were zero
                st.warning(
                    "تعداد کلمات برای بررسی از لیست تصادفی صفر انتخاب شده است.")
            elif not random_counts_defined and not final_words_to_process:  # Should not happen if "تصادفی" is selected
                st.warning("لطفا تعداد کلمات تصادفی را مشخص کنید.")

        # <-- کلید جدید اینجا هم اضافه شد
        elif word_source_key in ["منتخب طولانی", "منتخب ۵۰۰", "منتخب ۱۰۰ خلاقانه"]:
            if not words_to_check_from_source:
                st.error(
                    f"لیست کلمات {word_source_options[word_source_key]} بارگذاری نشده یا خالی است.")
            else:
                final_words_to_process.extend(words_to_check_from_source)

        if final_words_to_process:
            st.subheader(
                f"⏳ نتایج بررسی برای پسوند {domain_extension_val} (از لیست: {word_source_options[word_source_key]})")

            results_data = []
            total_words = len(final_words_to_process)
            progress_bar_check = st.progress(0)
            status_text_check = st.empty()
            processed_count_placeholder = st.empty()

            for idx, word_prefix in enumerate(final_words_to_process):
                full_domain = word_prefix + domain_extension_val
                status = check_domain_availability(full_domain)
                results_data.append({
                    "ردیف": idx + 1,
                    "کلمه": word_prefix,
                    "دامنه کامل": full_domain,
                    "وضعیت": status,
                    "طول کلمه": len(word_prefix)
                })

                progress = (idx + 1) / total_words
                progress_bar_check.progress(progress)
                status_text_check.text(f"در حال بررسی: {full_domain}")
                processed_count_placeholder.markdown(
                    f"**تعداد بررسی شده: {idx + 1} از {total_words}**")

            progress_bar_check.empty()
            status_text_check.success(f"✅ بررسی {total_words} دامنه کامل شد.")
            processed_count_placeholder.empty()

            if results_data:
                results_df = pd.DataFrame(results_data)

                st.markdown("---")
                st.subheader("📊 نمایش و مرتب‌سازی نتایج کلی")
                col_sort1, col_sort2 = st.columns(2)
                sort_by_column = col_sort1.selectbox(
                    "مرتب‌سازی نتایج بر اساس ستون:",
                    options=["ردیف", "کلمه", "دامنه کامل",
                             "وضعیت", "طول کلمه"],
                    index=0, key="sort_col_main"
                )
                sort_ascending = col_sort2.selectbox(
                    "ترتیب مرتب‌سازی:",
                    options=["صعودی", "نزولی"],
                    index=0, key="sort_order_main"
                )
                is_ascending = True if sort_ascending == "صعودی" else False

                if sort_by_column in ["ردیف", "طول کلمه"]:
                    results_df[sort_by_column] = pd.to_numeric(
                        results_df[sort_by_column])
                sorted_results_df = results_df.sort_values(
                    by=sort_by_column, ascending=is_ascending)

                st.dataframe(sorted_results_df, use_container_width=True, height=min(
                    35 * (len(sorted_results_df) + 1), 600))

                available_domains_summary_df = results_df[results_df["وضعیت"] == "Available"].copy(
                )
                if not available_domains_summary_df.empty:
                    available_domains_summary_df.reset_index(
                        drop=True, inplace=True)
                    available_domains_summary_df['ردیف نمایش'] = available_domains_summary_df.index + 1
                    st.success(
                        f"🎉 تعداد دامنه‌های آزاد یافت شده: {len(available_domains_summary_df)}")
                    with st.expander("مشاهده لیست دامنه‌های آزاد (قابل مرتب‌سازی با کلیک روی هدر ستون)"):
                        st.dataframe(available_domains_summary_df[[
                                     'ردیف نمایش', 'کلمه', 'دامنه کامل']], key='df_available', use_container_width=True)
                else:
                    st.info("ℹ️ هیچ دامنه آزادی در این بررسی یافت نشد.")

                registered_domains_summary_df = results_df[results_df["وضعیت"] == "Registered"].copy(
                )
                if not registered_domains_summary_df.empty:
                    registered_domains_summary_df.reset_index(
                        drop=True, inplace=True)
                    registered_domains_summary_df['ردیف نمایش'] = registered_domains_summary_df.index + 1
                    st.error(
                        f"🚫 تعداد دامنه‌های ثبت شده یافت شده: {len(registered_domains_summary_df)}")
                    with st.expander("مشاهده لیست دامنه‌های ثبت شده (قابل مرتب‌سازی با کلیک روی هدر ستون)"):
                        st.dataframe(registered_domains_summary_df[[
                                     'ردیف نمایش', 'کلمه', 'دامنه کامل']], key='df_registered', use_container_width=True)
                else:
                    st.info("ℹ️ هیچ دامنه ثبت شده‌ای در این بررسی یافت نشد.")

                saved_filename = save_results_to_json(
                    results_df, domain_extension_val, price_val, list_type_id_for_save)
                st.markdown(
                    f"💾 نتایج در فایل `{saved_filename}` ذخیره/به‌روزرسانی شد.")

        elif word_source_key == "تصادفی":
            # This condition is a bit tricky now due to locals() check.
            # We need to ensure that if "تصادفی" was chosen, but counts were zero, a message is shown.
            # The above checks inside the "تصادفی" block when populating final_words_to_process should cover this.
            # This outer elif might be redundant or needs refinement.
            if 'three_letter_count_to_check' in locals() and 'four_letter_count_to_check' in locals() and \
                    not (three_letter_count_to_check > 0 or four_letter_count_to_check > 0):
                st.warning(
                    "لطفاً تعداد کلمات برای بررسی (۳ حرفی یا ۴ حرفی) را بیشتر از صفر انتخاب کنید.")

        elif not final_words_to_process and word_source_key != "تصادفی":
            st.error(
                f"لیست کلمات '{word_source_options[word_source_key]}' برای پردازش خالی است.")


if __name__ == "__main__":
    main()
