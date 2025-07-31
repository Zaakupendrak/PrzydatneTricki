# -*- coding: utf-8 -*-
import os
import sys
from colorama import init, Fore, Style

# Inicjalizacja colorama dla wsparcia kolorów na Windows
init()

# Definiuj kolory
GREEN = Fore.GREEN
RED = Fore.RED
RESET = Style.RESET_ALL

# Funkcja do sprawdzania, czy string jest w pliku
def check_string_in_file(file_path, search_string):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if search_string in line:
                    return True
    except Exception as e:
        print(f"{RED}Error reading {file_path}: {e}{RESET}")
        return False
    return False

# Funkcja główna
def scan_directory(directory, search_strings):
    # Sprawdzenie, czy katalog istnieje
    if not os.path.isdir(directory):
        print(f"{RED}Error: '{directory}' is not a valid directory{RESET}")
        return

    # Sprawdzenie, czy lista ciągów nie jest pusta
    if not search_strings:
        print(f"{RED}Error: No search strings provided{RESET}")
        return

    # Lista dozwolonych rozszerzeń (można dostosować)
    allowed_extensions = {".ts", '.tsx'}

    for s in search_strings:
        found = False
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                # Sprawdzanie rozszerzenia pliku
                if os.path.splitext(file)[1].lower() in allowed_extensions:
                    found = check_string_in_file(file_path, s)
                    if found:
                        break
            if found:
                print(f"{GREEN}String '{s}' found in {file_path}{RESET}")
                break
        else:
            print(f"{RED}String '{s}' NOT found{RESET}")

# Przykład użycia
if __name__ == "__main__":
    directory = "/Users/zaak/Downloads/labels_1-1-30v2.csv"
    search_strings = ["accordion_cookie_desc", "accordion_cookie_ttl", "app_ttl_bl", "app_ttl_inactive", "app_ttl", "are_you_sure", "aria_amount", "aria_language_expand", "aria_select_bank", "aria_select_language", "aria_t6", "aria_trx_desc", "aria_v9_pass", "back", "bl_amt_suffix", "btn_dlg_cancelconfirm", "bl_btn_dlg_cancel_return", "bl_btn_dlg_guide_close", "bl_btn_dlg_info_ftr_close", "bl_btn_fallback_blik", "bl_btn_guide", "bl_info_ftr_1", "bl_btn_info_ftr_1", "bl_info_ftr_2", "bl_btn_info_ftr_2", "bl_different_way_to_pay", "bl_dlg_guide_sdesc_1", "bl_dlg_guide_sdesc_2", "bl_dlg_guide_sdesc_3", "bl_dlg_guide_fnf_sdesc_1", "bl_dlg_guide_fnf_sdesc_2", "bl_dlg_guide_fnf_sdesc_3", "bl_dlg_guide_sttl_1", "bl_dlg_guide_sttl_2", "bl_dlg_guide_sttl_3", "bl_dlg_guide_ttl", "bl_dlg_info_desc", "bl_dlg_info_ftr_splr_1", "bl_dlg_info_ftr_splr_1_sttl_1", "bl_dlg_info_ftr_splr_1_sttl_2", "bl_dlg_info_ftr_splr_1_sdesc_2", "bl_dlg_info_ftr_splr_1_sttl_3", "bl_dlg_info_ftr_splr_1_sdesc_3", "bl_dlg_info_ftr_splr_2", "bl_dlg_info_ftr_splr_2_sttl_1", "bl_dlg_info_ftr_splr_2_sdesc_1", "bl_dlg_info_ftr_splr_2_sttl_2", "bl_dlg_info_ftr_splr_2_sdesc_2", "bl_dlg_info_ftr_splr_2_sttl_3", "bl_dlg_info_ftr_splr_2_sdesc_3", "bl_dlg_info_ftr_splr_2_sttl_4", "bl_btn_info_ftr_splr_2_collapse", "bl_btn_info_ftr_splr_2_expand", "bl_dlg_info_ftr_splr_2_sdesc_4", "bl_dlg_info_ftr_splr_2_sdesc_5", "bl_dlg_info_ttl", "bl_dlg_where_get_code_desc", "bl_dlg_where_get_code_fnf_desc", "bl_err_active_in_another_bank_ttl", "bl_err_dataamt_huge_ttl", "bl_err_default_desc", "bl_err_limit_exceeded_desc", "bl_err_limit_exceeded_ttl", "bl_err_limit_locked_ttl", "bl_err_limit_not_approved_ttl", "bl_err_low_limit_desc", "bl_err_low_limit_ttl", "bl_err_not_supported_ttl", "bl_err_outofservice_ttl", "bl_err_pesel_restricted_desc", "bl_err_pesel_restricted_ttl", "bl_err_pesel_service_failed_desc", "bl_err_pesel_service_failed_ttl", "bl_generate_code_in_app", "bl_header_h1_confirm_payment", "bl_header_h1", "bl_info_ftr", "bl_repeat_activation", "bl_success_ttl", "bl_try_with_bank_desc", "btn_cancel", "btn_close", "btn_cookie_expand", "btn_cookie_more", "btn_dlg_cancel_close", "btn_dlg_cancel_return", "btn_dlg_no_code_close", "btn_dlg_where_get_code_close", "btn_forward", "btn_no_code_accept", "btn_pay_with_code", "btn_try_again", "btn_where_get_code", "btn_why_no_code_required", "come_back_to_service", "come_back_to_store", "completed", "confirm_payment", "dlg_cancel_desc", "dlg_cancel_ttl", "dlg_no_code_desc_1", "dlg_no_code_desc_2_1", "dlg_no_code_desc_2_2", "dlg_no_code_desc_2_3", "dlg_no_code_desc_3", "dlg_no_code_desc_4", "dlg_no_code_sdesc", "dlg_no_code_sttl", "dlg_no_code_ttl", "dlg_where_get_code_desc", "dlg_where_get_code_ttl", "account_closed_error", "account_disabled_error", "err_cancelled_ttl", "err_dataamt_pos_desc", "err_dataamt_pos_ttl", "err_ended_ttl", "general_blik_error", "err_old_apk_desc", "err_payment_not_succeded_ttl", "err_something_wrong", "alias_declined_error", "app_origin_not_de", "app_origin_not_pl", "app_origin_not_ro", "app_origin_not_sk", "bad_pin_error", "trx_business_error", "invalid_blikcode_length", "err_t6_code_required", "out_of_service_error", "t6_trx_error", "er_tas_200", "er_tas_500", "t6_trx_timeout_error", "user_declined_error", "v9_trx_error", "err_t6_v9_pass_required", "err_t6_wrong_code", "v9_wrong_ticket_error", "wrong_check_value", "wrong_ticket_error", "err_t6_wrong_v9_value", "er_tic_used_error", "err_transaction_not_completed_ttl", "err_try_again_desc", "err_ups_ttl", "err_you_resigned_ttl", "finish_process", "header_h1_confirm_payment", "header_h1", "info_ftr", "into_bank_app", "paying_through_mobile", "payment_confirmation_not_accepted", "payment_revoked_on_mobile", "payment_without_code", "place_holder_pass", "place_holder_t6", "place_holder_v9", "success_desc", "success_ttl"]

    scan_directory(directory, [s.strip() for s in search_strings])
