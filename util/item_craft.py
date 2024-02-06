import re
import os
import sys
import yaml
from craft_util import *

ENCHANT     = 99

script_dir = os.path.dirname(os.path.abspath(__file__))


def loadItemList():
    pattern = r'\[(\d+),(\d+),\d+,\d+,\d+,\d+,\d+,\d+,([^,]*),[^,]*,[^,]*,[^]]*0\]'
    with open(f'{script_dir}/../roro/m/js/item.dat.js', 'r', encoding='utf-8') as file:
        js_code = file.read()
    matches = re.findall(pattern, js_code)
    return [[int(id), name.replace('"',''), int(type)] for id, type, name in matches]


def loadSlotInfoList():
    pattern = r'\[(\d+),-1,0,0,\[\["([^"]+)","([^"]+)"]],\[],\[\[\[174,\[50,\[(\d+)]]],.+\[]]'
    with open(f'{script_dir}/../roro/m/js/data/mig.enchlist.dat.js', 'r', encoding='utf-8') as file:
        js_code = file.read()
    matches = re.findall(pattern, js_code)
    return [[int(id), name, code] for id, name, code, item_id in matches]


def loadItemDict():
    pattern = r'\[(\d+),(\d+),\d+,\d+,\d+,\d+,\d+,\d+,([^,]*),[^,]*,[^,]*,[^]]*0\]'
    with open(f'{script_dir}/../roro/m/js/item.dat.js', 'r', encoding='utf-8') as file:
        js_code = file.read()
    matches = re.findall(pattern, js_code)
    return  {name.replace('"',''): int(id) for id, type, name in matches if type != "100"}    


def getEnchantDict(enchant_list):
    return {item[1]: item[0] for item in enchant_list}


def getId(name, list):
    lookup_dict_reverse = {item[1]: item[0] for item in list}
    return lookup_dict_reverse.get(name)


def getLatestId(list):
    return max([entity[0] for entity in list])


def getEnchantTypeCode(name, slotinfo_list):
    lookup_dict_reverse = {item[1]: item[2] for item in slotinfo_list}
    return lookup_dict_reverse.get(name)


ITEM_CODE = loadItemDict()

 
# -----------------------------------
# 初期化
# -----------------------------------
item_list = loadItemList()
enchant_list = loadEnchantList()
slotinfo_list = loadSlotInfoList()
equipment_type_list = loadEquipmentTypeDict()
enchant_dict = getEnchantDict(enchant_list)
capability_dict = loadCapabilityDict()
equipable_dict = loadEquipableCodeDict()

if __name__ == "__main__":
    
    item_dat_js = []
    itemset_dat_js = []
    mig_enchlist_dat_js = []

    item_id = getLatestItemId()
    itemset_id = getLatestIdFromItemSet()
    enchant_id = getLatestId(slotinfo_list)
    
    with open(f'{script_dir}/item.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    for item_info in config['item_list']:

    # ------------------------------------------------------
    #  item.dat.js
    # ------------------------------------------------------

        # アイテム基本性能の出力
        item_id += 1
        base_id = item_id
        equipment_type = equipment_type_list.get(item_info["type"])
        equipable_code = equipable_dict.get(item_info["required_job"])
        description = ""
        if 'desc' in item_info:
            description = item_info['desc']
        record  = f'ItemObjNew[{item_id}] = [{item_id},{equipment_type},{equipable_code},{item_info["atk_or_def"]},{item_info["weapon_lv"]},'
        record += f'{item_info["slot"]},{item_info["weight"]},{item_info["required_lv"]},'
        record += f'"{item_info["name"]}","{item_info["yomi"]}","{description}",'
        for capability in item_info['capabilities']:
            record += buildCapabilityRecord(capability)
        record += "0];"
        item_dat_js.append(record)

        # item.dat.js に記述すべきセット効果の出力
        if 'set_list' in item_info:
            item_to_set_record = f"ItemIdToSetIdMap[{base_id}] = ["
            for set_info in item_info['set_list']:
                item_id += 1
                record  = f'ItemObjNew[{item_id}] = [{item_id},100,0,0,0,0,0,0,0,0,"",'
                for capability in set_info['capabilities']:
                    record += buildCapabilityRecord(capability)
                record += "0];"
                item_dat_js.append(record)

        # ------------------------------------------------------
        #  itemset.dat.js
        # ------------------------------------------------------
                
                # セット条件の出力
                itemset_id += 1
                record = f"w_SE[{itemset_id}] = [{item_id},{base_id},"
                for entity in set_info['entity_list']:
                    set_entity_id = ITEM_CODE.get(entity['item_name']) if 'item_name' in entity else CARD_OR_ENCH_CODE.get(entity['card_name']) * -1
                    record += f"{set_entity_id},"
                # EOF
                record += "];"
                itemset_dat_js.append(record)
                item_to_set_record += f"{itemset_id},"
            # EOF                
            item_to_set_record += f"];"
            itemset_dat_js.append(item_to_set_record)

        # ------------------------------------------------------
        #  mig.enchlist.dat.js
        # ------------------------------------------------------
        if 'enchant' in item_info:
            for enchant in item_info['enchant']:
                enchant_id += 1
                record = buildEnchantRecord(base_id, enchant_id, enchant)
                mig_enchlist_dat_js.append(record)
                record = f'g_constDataManager.enchListDataManager.reverseResolveArrayItemId[{base_id}] = [{enchant_id}];'
                mig_enchlist_dat_js.append(record)

    OUTPUT_FILE = [
        ('item.dat.js', item_dat_js),
        ('itemset.dat.js', itemset_dat_js),
        ('mig.enchlist.dat.js', mig_enchlist_dat_js),
    ]
    for file_name, data_array in OUTPUT_FILE:
        print(f"--- {file_name} ---")
        for record in data_array:
            if 'None' in record:
                print('エラー: 空のデータが挿入されています')
                print(record)
                sys.exit(0)
        with open(f"{script_dir}/output_{file_name}", "w", encoding="utf-8") as f:
            f.write("\n".join(data_array))
