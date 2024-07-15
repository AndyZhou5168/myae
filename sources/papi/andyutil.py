#!/usr/bin/env python3
#coding=utf-8

"""
    Created on: 2022-05-08 by AndyZhou
"""

import re, hashlib, os
from time import time, strftime, localtime
from functools import wraps
from struct import pack, unpack
from socket import ntohl, inet_aton
from subprocess import getstatusoutput as mycmd


class Util(object):
    MAP_SIZE, SOCKET_READ_CHUNK, unique_id_base = 65536, 1024, None

    @staticmethod
    def time_me(info="perf", perf=None):
        def _time_me(fn):
            @wraps(fn)
            def _wrapper(*args, **kwargs):
                start = time()
                rlt = fn(*args, **kwargs)
                perf_info = "方法【%s】耗时关键词【%s】: [%.3f] sec" %(fn.__name__, info, time()-start)
                if perf is not None:
                    perf['perf'] = perf_info
                else:
                    print(perf_info)
                return rlt
            return _wrapper
        return _time_me


    @staticmethod
    def time_me2(info="perf", perf=None):
        def _time_me(fn):
            @wraps(fn)
            def _wrapper(*args, **kwargs):
                start = time()
                fn(*args, **kwargs)
                perf_info = "方法【%s】耗时关键词【%s】: [%.3f] sec" %(fn.__name__, info, time()-start)
                if perf is not None:
                    perf['perf'] = perf_info
                else:
                    print(perf_info)
            return _wrapper
        return _time_me


    @staticmethod
    def trans_data_impl(data, isz):
        ex = None

        try:
            if isz:
                import zlib, json
                if data:
                    if 1 == isz:
                        return json.dumps(''.join(['%02x' %i for i in zlib.compress(data.encode('utf8'), level=9)]))
                    if 2 == isz:
                        return zlib.decompress(bytearray.fromhex(json.loads(data))).decode()
            return data
        except (Exception) as e:
            ex = e

        print("处理仿真送回的桩点数据异常【", ex, "】")
        return None


    @staticmethod
    def gen_report(pmap_size, status_code, data):
        '''1 + 1024 * 64'''
        print("收到仿真送回的桩点原始数据【%s】" %data)

        map_size = pmap_size
        r1 = bytearray(1)
        r2 = bytearray(map_size)

        r1[0] = status_code
        if data:
            data0 = data.split(',')
            data0 = [i for i in data0 if len(i)>0]
            data0 = [re.sub(r'\s+', '', i) for i in data0]
            len0 = len(data0)

            data1 = [i for i in data0 if i.isdigit()]
            data1 = [int(i) for i in data1]
            data1 = [i for i in data1 if i<=65536 and i>=0]
            len1 = len(data1)
            print("处理仿真送回的桩点结果数据【%s】" %str(data1).replace(' ', '')[1:-1])

            if len0 == len1:
                Util.cal_bitmap(data1, r2, map_size)
            else:
                print("点位数据异常【", data, "】")

        return bytes(r1), bytes(r2)


    @staticmethod
    def cal_bsid(data, bitlen=16):
        model_base = 2**bitlen - 1

        func_id = (data & 0xfff) >> 1
        inst_id = ((data & 0x000ff000) >> 12) & 0x0007f
        real_id = ((func_id << 7) & 0x3ff80) | inst_id

        return (real_id & model_base)


    @staticmethod
    def cal_bitmap(data1, r2, map_size, logbsid=True, logpos=True):
        prev_loc = 0
        for i in data1:
            cur_loc = i
            cur_loc  = (cur_loc >> 4) ^ (cur_loc << 8)
            cur_loc &= (map_size - 1)
            if cur_loc < map_size:
                position = cur_loc ^ prev_loc
                if r2[position] == 255:
                    if logpos:
                        print("position r2[%-7d]已到255，不再累加" %position)
                else:
                    r2[position] += 1
                if logbsid:
                    print("position: [%-7d]^[%-7d] => [%-7d]:[%-3d]" %(cur_loc, prev_loc, position, r2[position]))
                prev_loc = cur_loc >> 1


    @staticmethod
    def print_b16(data):
        tmp = ["%02X" %i for i in data]
        return ' '.join(tmp)


    @staticmethod
    def make_cb_data(msg_type, taskid, data=None):
        return {"msg_type":msg_type, "data":data, "task_instances_id":"%d" %taskid}


    @staticmethod
    def get_unique_id():
        if not Util.unique_id_base:
            Util.unique_id_base = int(time()) & 0xffffffff

        Util.unique_id_base += 1
        #print("生成的唯一ID：", Util.unique_id_base)
        return Util.unique_id_base


    @staticmethod
    def trans_ipport_4B2B(data):
        data = data.split(':')
        lip = data[0]

        if lip=='0.0.0.0' or lip=='127.0.0.1' or lip=='localhost':
            lip = mycmd(r"ip -o -4 addr|awk -F ' ' '{print $4}'|sed 's/\/[0-9]\{1,3\}//g'|grep -vP '127|172'|grep -P '192.168|10.1'")[1]
        if not lip:
            lip = os.getenv('HOSTIP')
        print("注册到仿真的地址【%s:%s】" %(lip, data[1]))

        ip_int0 = ntohl(unpack("<I", inet_aton(lip))[0])
        ip_int = pack('<I', ip_int0)
        port_int0 = int(data[1])
        port_int = pack('<H', port_int0)

        return ip_int, port_int, ip_int0, port_int0


    @staticmethod
    def trans_to_judge_1B4B1B(data):
        data = data.split(',')
        tmp = bytearray(6)

        tmp[0] = int(data[0])
        tmp[1:5] = pack('<I', int(data[1]))
        tmp[5] = int(data[2])

        return bytes(tmp)


    @staticmethod
    def trans_to_fc_bsid_1B1B(data):
        data = data.split(',')
        tmp = bytearray(len(data))

        tmp[0] = int(data[0])
        tmp[1] = int(data[1])
        tmp[2] = int(data[2])
        tmp[3] = int(data[3])

        return bytes(tmp)


    @staticmethod
    def gen_fmt_ts():
        return strftime(r"%y%m%d%H%M%S", localtime())


    crc_seed = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
        0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
        0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
        0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
        0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
        0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
        0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
        0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
        0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
        0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
        0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
        0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
        0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
        0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
        0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
        0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
        0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
        0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
        0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
        0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
        0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
        0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
        0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0,
    ]


    @staticmethod
    def crc_cal(read_data):
        crc_verf = 0
        for i in read_data:
            crc_verf = ((crc_verf << 8) & 0xFF00) ^ Util.crc_seed[(i ^ (crc_verf >> 8)) & 0x00FF]

        return crc_verf


    @staticmethod
    def gen_sha1(content):
        return Util.__gen_df_impl(content, None)


    @staticmethod
    def gen_md5(content):
        return Util.__gen_df_impl(content)


    @staticmethod
    def __gen_df_impl(content, algo="md5"):
        dfobj = hashlib.md5() if algo == "md5" else hashlib.sha1()
        dfobj.update(content)
        return dfobj.hexdigest()


if __name__ == '__main__':
    print("MD5 digital finger: 【%s】" %Util.gen_md5("have a nice day and daydayup".encode('utf8')))
    print("SHA1 digital finger: 【%s】\n" %Util.gen_sha1("have a nice day and daydayup".encode('utf8')))

    tmp1, tmp2, tmp3, tmp4 = Util.trans_ipport_4B2B("119.3.153.134:7018")
    print(Util.print_b16(tmp1))
    print(Util.print_b16(tmp2))
    print(tmp3)
    print(tmp4)

    tmp = 'have a nice day'.encode('utf8')
    tmp = Util.crc_cal(tmp)
    print(tmp, ", ", hex(tmp))

    tmp = b'\x91'
    tmp = Util.crc_cal(tmp)
    print(tmp, ", ", hex(tmp))

    tmp = bytearray(11)
    tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], tmp[5], tmp[6], tmp[7], tmp[8], tmp[9], tmp[10] = 0x9c, 0x00, 0x00, 0x00, 0x00, 0x08, 0x20, 0x00, 0x00, 0x00, 0x03
    tmp = Util.crc_cal(tmp)
    print(tmp, ", ", hex(tmp))

    tmp5 = []
    for i in range(1000000):
        tmp5.append(Util.get_unique_id())
    tmp0 = []
    for i in range(1000000):
        tmp0.append(Util.get_unique_id())
    tmp0 = set(tmp0)
    tmp5 = set(tmp5)
    print("ID唯一性测试1：", len(tmp0)==1000000, len(tmp0))
    print("ID唯一性测试2：", len(tmp5)==1000000, len(tmp5))
    print("ID唯一性测试3：", len(tmp0 & tmp5) == 0)
