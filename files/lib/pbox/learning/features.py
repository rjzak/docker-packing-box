# -*- coding: UTF-8 -*-
from ast import literal_eval
from collections import OrderedDict
from functools import cached_property
from tinyscript.helpers import entropy, execute_and_log as run

from ..utils import expand_categories


__all__ = ["Features", "FEATURE_DESCRIPTIONS"]


FEATURE_DESCRIPTIONS = {}
FEATURES = {
    'All': {
        'entropy': lambda exe: entropy(exe.read_bytes()),
    },
    'PE': {
        'pefeats': lambda exe: pefeats(exe),
    },
}


PEFEATS = __d = OrderedDict()
__d['dll_characteristics_1'] = "DLLs characteristics 1"
__d['dll_characteristics_2'] = "DLLs characteristics 2"
__d['dll_characteristics_3'] = "DLLs characteristics 3"
__d['dll_characteristics_4'] = "DLLs characteristics 4"
__d['dll_characteristics_5'] = "DLLs characteristics 5"
__d['dll_characteristics_6'] = "DLLs characteristics 6"
__d['dll_characteristics_7'] = "DLLs characteristics 7"
__d['dll_characteristics_8'] = "DLLs characteristics 8"
__d['checksum'] = "Checksum"
__d['image_base'] = "Image Base"
__d['base_of_code'] = "Base of Code"
__d['os_major_version'] = "OS Major version"
__d['os_minor_version'] = "OS Minor version"
__d['size_of_image'] = "Size of Image"
__d['size_of_code'] = "Size of Code"
__d['headers'] = "Headers"
__d['size_of_initializeddata'] = "Size Of InitializedData"
__d['size_of_uninitializeddata'] = "Size Of UninitializedData"
__d['size_of_stackreverse'] = "Size Of StackReserve"
__d['size_of_stack_commit'] = "Size of Stack Commit"
__d['section_alignment'] = "Section Alignment"
__d['number_standard_sections'] = "number of standards sections the PE holds"
__d['number_non_standard_sections'] = "number of non-standards sections the PE holds"
__d['ratio_standard_sections'] = "ratio between the number of standards sections found and the number of all sections" \
                                 " found in the PE under analysis"
__d['number_x_sections'] = "number of Executable sections the PE holds"
__d['number_w_sections'] = "number of Writable sections the PE holds"
__d['number_wx_sections'] = "number of Writable and Executable sections the PE holds"
__d['number_rx_sections'] = "number of readable and executable sections"
__d['number_rw_sections'] = "number of readable and writable sections"
__d['number_rwx_sections'] = "number of Writable and Readable and Executable sections the PE holds"
__d['code_section_x'] = "code section is not executable"
__d['x_section_is_not_code'] = "executable section is not a code section"
__d['code_section_not_present'] = "code section is not present in the PE under analysis"
__d['ep_not_in_code_section'] = "EP is not in the code section"
__d['ep_not_in_standard_section'] = "EP is not in a standard section"
__d['ep_not_x_section'] = "EP is not in an executable section"
__d['ep_ratio'] = "EP ratio between raw data and virtual size for the section of entry point"
__d['number_sections_size_0'] = "number of sections having their physical size =0 (size on disk)"
__d['number_sections_vsize>dsize'] = "number of sections having their virtual size greater than their raw data size"
__d['max_ratio_rdata'] = "maximum ratio raw data per virtual size among all the sections"
__d['min_ratio_rdata'] = "minimum ratio raw data per virtual size among all the sections"
__d['address_to_rdata_not_conform'] = "address pointing to raw data on disk is not conforming with the file alignement"
__d['entropy_code_sections'] = "entropy of Code/text sections"
__d['entropy_data_section'] = "entropy of data section"
__d['entropy_resource_section'] = "entropy of resource section"
__d['entropy_pe_header'] = "entropy of PE header"
__d['entropy'] = "entropy of the whole executable"
__d['entropy_section_with_ep'] = "entropy of section holding the Entry point (EP) of the PE under analysis"
__d['byte_0_after_ep'] = "byte 0 following the EP"
__d['byte_1_after_ep'] = "byte 1 following the EP"
__d['byte_2_after_ep'] = "byte 2 following the EP"
__d['byte_3_after_ep'] = "byte 3 following the EP"
__d['byte_4_after_ep'] = "byte 4 following the EP"
__d['byte_5_after_ep'] = "byte 5 following the EP"
__d['byte_6_after_ep'] = "byte 6 following the EP"
__d['byte_7_after_ep'] = "byte 7 following the EP"
__d['byte_8_after_ep'] = "byte 8 following the EP"
__d['byte_9_after_ep'] = "byte 9 following the EP"
__d['byte_10_after_ep'] = "byte 10 following the EP"
__d['byte_11_after_ep'] = "byte 11 following the EP"
__d['byte_12_after_ep'] = "byte 12 following the EP"
__d['byte_13_after_ep'] = "byte 13 following the EP"
__d['byte_14_after_ep'] = "byte 14 following the EP"
__d['byte_15_after_ep'] = "byte 15 following the EP"
__d['byte_16_after_ep'] = "byte 16 following the EP"
__d['byte_17_after_ep'] = "byte 17 following the EP"
__d['byte_18_after_ep'] = "byte 18 following the EP"
__d['byte_19_after_ep'] = "byte 19 following the EP"
__d['byte_20_after_ep'] = "byte 20 following the EP"
__d['byte_21_after_ep'] = "byte 21 following the EP"
__d['byte_22_after_ep'] = "byte 22 following the EP"
__d['byte_23_after_ep'] = "byte 23 following the EP"
__d['byte_24_after_ep'] = "byte 24 following the EP"
__d['byte_25_after_ep'] = "byte 25 following the EP"
__d['byte_26_after_ep'] = "byte 26 following the EP"
__d['byte_27_after_ep'] = "byte 27 following the EP"
__d['byte_28_after_ep'] = "byte 28 following the EP"
__d['byte_29_after_ep'] = "byte 29 following the EP"
__d['byte_30_after_ep'] = "byte 30 following the EP"
__d['byte_31_after_ep'] = "byte 31 following the EP"
__d['byte_32_after_ep'] = "byte 32 following the EP"
__d['byte_33_after_ep'] = "byte 33 following the EP"
__d['byte_34_after_ep'] = "byte 34 following the EP"
__d['byte_35_after_ep'] = "byte 35 following the EP"
__d['byte_36_after_ep'] = "byte 36 following the EP"
__d['byte_37_after_ep'] = "byte 37 following the EP"
__d['byte_38_after_ep'] = "byte 38 following the EP"
__d['byte_39_after_ep'] = "byte 39 following the EP"
__d['byte_40_after_ep'] = "byte 40 following the EP"
__d['byte_41_after_ep'] = "byte 41 following the EP"
__d['byte_42_after_ep'] = "byte 42 following the EP"
__d['byte_43_after_ep'] = "byte 43 following the EP"
__d['byte_44_after_ep'] = "byte 44 following the EP"
__d['byte_45_after_ep'] = "byte 45 following the EP"
__d['byte_46_after_ep'] = "byte 46 following the EP"
__d['byte_47_after_ep'] = "byte 47 following the EP"
__d['byte_48_after_ep'] = "byte 48 following the EP"
__d['byte_49_after_ep'] = "byte 49 following the EP"
__d['byte_50_after_ep'] = "byte 50 following the EP"
__d['byte_51_after_ep'] = "byte 51 following the EP"
__d['byte_52_after_ep'] = "byte 52 following the EP"
__d['byte_53_after_ep'] = "byte 53 following the EP"
__d['byte_54_after_ep'] = "byte 54 following the EP"
__d['byte_55_after_ep'] = "byte 55 following the EP"
__d['byte_56_after_ep'] = "byte 56 following the EP"
__d['byte_57_after_ep'] = "byte 57 following the EP"
__d['byte_58_after_ep'] = "byte 58 following the EP"
__d['byte_59_after_ep'] = "byte 59 following the EP"
__d['byte_60_after_ep'] = "byte 60 following the EP"
__d['byte_61_after_ep'] = "byte 61 following the EP"
__d['byte_62_after_ep'] = "byte 62 following the EP"
__d['byte_63_after_ep'] = "byte 63 following the EP"
__d['number_dll_imported'] = "number of DLLs imported"
__d['number_func_imported_in_idt'] = "number of functions imported found in the import table directory (IDT)"
__d['number_malicious_api_imported'] = "number of malicious APIs imported"
__d['ratio_malicious_api_imported'] = "ratio between the number of malicious APIs imported to the number of all " \
                                      "functions imported by the PE"
__d['number_addresses_in_iat'] = "number of addresses (corresponds to functions) found in the import address table " \
                                 "(IAT)"
__d['debug_dir_present'] = "debug directory is present or not"
__d['number_resources'] = "number of resources the PE holds"
FEATURE_DESCRIPTIONS.update(PEFEATS)


def pefeats(executable):
    """ This uses pefeats to extract 119 features from PE files. """
    out, err, retc = run("pefeats %s" % executable)
    if retc == 0:
        return {f: literal_eval(v) for f, v in zip(PEFEATS.keys(), out.decode().strip().split(",")[1:])}


class Features(dict):
    """ This class represents the dictionary of features valid for a given list of executable categories. """
    def __init__(self, *categories):
        categories, all_categories = expand_categories(*categories), expand_categories("All")
        # consider most generic features first
        for category, features in FEATURES.items():
            if category in all_categories:
                continue
            for subcategory in expand_categories(category):
                if subcategory in categories:
                    for name, func in features.items():
                        self[name] = func
        # then consider most specific ones
        for category, features in FEATURES.items():
            if category not in all_categories or category not in categories:
                continue
            for name, func in features.items():
                self[name] = func

