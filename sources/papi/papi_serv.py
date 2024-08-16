#!/usr/bin/env python3
#coding=utf-8

"""
    Created on: 2024-07-15 by AndyZhou
"""

import os, logging, json, redis, sysv_ipc, struct
from andylog import Andylog
from andyutil import Util
from subprocess import getstatusoutput as mycmd
from traceback import format_exc as exinfo
from flask import Flask, jsonify, request, make_response, abort


app = Flask(__name__)
penv = {
    'andylog'           : Andylog(),
    'firmwares'         : 'firm-md5-set',
    'apirunning'        : False,
    'processid'         : None,
    'url_prefix'        : '/myae/api/v1/yishi/',
    'upload_dir'        : '/home/andy/myae/share',
    'work_dir'          : '/opt/myae/firmwares',
    'sysv_shm_valve'    : 2**30,
    'sysv_shm'          : {},
}
logging.getLogger('werkzeug').setLevel(logging.INFO)

@app.before_request
def log_request():
    print(f'\n===> req method: {request.method}, req path: {request.path}, req data: {request.get_data().decode("utf-8")}\n')
    pass

@app.after_request
def log_response(response):
    #print(f'\n<=== resp status code: {response.status_code}, resp data: {response.get_data()}\n')
    return response


@app.route(penv['url_prefix']+'simu/network/', methods=['POST', 'GET'])
@Util.time_me()
def action_simu_network():
    """
        【网络功能模拟】
        操纵pNET参数处理
    """
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        ok, simuNet = __action_simu_check('simuNet')
        if not ok:
            return make_response(simuNet, 200)

        simuNet = "true" if simuNet == 1 else "false"
        penv['rc'][0].hset('myae-params', 'pNET', simuNet)
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'simu/peri/', methods=['POST', 'GET'])
@Util.time_me()
def action_simu_peri():
    """
        【设备外设模拟】
        操纵pNVRAM参数处理
    """
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        ok, simuPeri = __action_simu_check('simuPeri')
        if not ok:
            return make_response(simuPeri, 200)

        simuPeri = "true" if simuPeri == 1 else "false"
        penv['rc'][0].hset('myae-params', 'pNVRAM', simuPeri)
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'simu/param/', methods=['POST', 'GET'])
@Util.time_me()
def action_simu_param():
    """
        【缺失参数模拟】
        操纵pASLR参数处理
    """
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        ok, simuParam = __action_simu_check('simuParam')
        if not ok:
            return make_response(simuParam, 200)

        penv['rc'][0].hset('myae-params', 'pASLR', simuParam)
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'simu/lostfile/', methods=['POST', 'GET'])
@Util.time_me()
def action_simu_lostfile():
    """
        【缺失系统文件模拟】
        操纵868固件中缺失的/etc/hosts文件处理
    """
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        ok, simuLostfile = __action_simu_check('simuLostfile')
        if not ok:
            return make_response(simuLostfile, 200)

        penv['rc'][0].hset('myae-params', 'simuLostfile', simuLostfile)
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'simu/stdio/', methods=['POST', 'GET'])
@Util.time_me()
def action_simu_stdio():
    """
        【标准输入输出模拟】
        操纵QEMU的stdio参数处理
    """
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        ok, simuStdio = __action_simu_check('simuStdio')
        if not ok:
            return make_response(simuStdio, 200)

        penv['rc'][0].hset('myae-params', 'simuStdio', simuStdio)
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'simu/desc/', methods=['POST', 'GET'])
@Util.time_me()
def action_simu_desc():
    """场景模拟接口说明"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        data = """
            （1）模拟场景的参数：
                    需整型 或 字符串；
                    取值0 或 1；
                    1-打开模拟、0-关闭模拟；
            （2）各模拟场景使用参数：
                    网络功能模拟(320)：    simuNet；
                    设备外设模拟(868)：    simuPeri；
                    缺失参数模拟(320)：    simuParam；
                    缺失系统文件模拟(320)：simuLostfile；
                    标准输入输出模拟(320)：simuStdio；
            （3）每种模拟场景操作时执行的次序：
                    停止引擎-->清理引擎-->所有模拟开关置1；
                    该场景模拟开关置0-->运行引擎-->观察结果：
                        超过耗时最大经验阈值 或 程序中途退出；
                    ****************************************
                    停止引擎-->清理引擎-->所有模拟开关置1；
                    该场景模拟开关置1(可省略)-->运行引擎-->观察结果；
                        一般在耗时最大经验阈值内运行成功；
            （4）目前3个标靶固件模拟概述：
                    4C/4GB资源，最大耗时(单位：分钟)累次观察众数值：
                        320(10) < 868(15) < 820(25)；
                    标320的场景，一般意味着对868、820也适用；
                    演示时，一般以标注的固件为优先；
            （5）所有场景模拟完成-->所有模拟开关置1；
        """.replace('\\n', '\n')
        return make_response(jsonify({'code': 1, 'data': data, 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


def __action_simu_check(pname):
    tmp = request.form.get(pname, None)

    if tmp is None:
        return False, jsonify({'code': 1001, 'data': '', 'msg': f'{pname}字段缺失',})

    if not isinstance(tmp, int):
        if isinstance(tmp, str) and tmp.isdigit():
            tmp = int(tmp)
    if not isinstance(tmp, int):
        return False, jsonify({'code': 1001, 'data': '', 'msg': f'{pname}字段要求整型或字符串型',})

    if tmp not in [0, 1]:
        return False, jsonify({'code': 1001, 'data': '', 'msg': f'{pname}字段取值要求0或1',})

    return True, tmp


@app.route(penv['url_prefix']+'params/desc/', methods=['POST', 'GET'])
@Util.time_me()
def action_query_param1():
    """查询参数说明"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        data = {
            'pBOOT'     : '启动',
            'pNET'      : '网络',
            'pNVRAM'    : '存储',
            'pKERNEL'   : '内核',
            'pETC'      : '其他',
            'pASLR'     : 'ASLR',
            'pTM1'      : '等待超时1',
            'pTM2'      : '等待超时2',
            'pCTM1'     : '检测超时1',
            'pCTM2'     : '检测超时2',
        }
        return make_response(jsonify({'code': 1, 'data': str(data), 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'params/list/', methods=['POST', 'GET'])
@Util.time_me()
def action_query_param2():
    """查询参数值"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        rc = penv['rc'][0]
        data = {
            'pBOOT'     : rc.hget('myae-params', 'pBOOT'),
            'pNET'      : rc.hget('myae-params', 'pNET'),
            'pNVRAM'    : rc.hget('myae-params', 'pNVRAM'),
            'pKERNEL'   : rc.hget('myae-params', 'pKERNEL'),
            'pETC'      : rc.hget('myae-params', 'pETC'),
            'pASLR'     : rc.hget('myae-params', 'pASLR'),
            'pTM1'      : rc.hget('myae-params', 'pTM1'),
            'pTM2'      : rc.hget('myae-params', 'pTM2'),
            'pCTM1'     : rc.hget('myae-params', 'pCTM1'),
            'pCTM2'     : rc.hget('myae-params', 'pCTM2'),
        }
        return make_response(jsonify({'code': 1, 'data': str(data), 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'params/up/', methods=['POST', 'GET'])
@Util.time_me()
def action_up_params():
    """更新参数值"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        data0 = {}

        pBOOT = request.form.get('pBOOT', None)
        if pBOOT: data0['pBOOT'] = pBOOT

        pNET = request.form.get('pNET', None)
        if pNET: data0['pNET'] = pNET

        pNVRAM = request.form.get('pNVRAM', None)
        if pNVRAM: data0['pNVRAM'] = pNVRAM

        pKERNEL = request.form.get('pKERNEL', None)
        if pKERNEL: data0['pKERNEL'] = pKERNEL

        pETC = request.form.get('pETC', None)
        if pETC: data0['pETC'] = pETC

        pASLR = request.form.get('pASLR', None)
        if pASLR: data0['pASLR'] = pASLR

        pTM1 = request.form.get('pTM1', None)
        if pTM1: data0['pTM1'] = pTM1

        pTM2 = request.form.get('pTM2', None)
        if pTM2: data0['pTM2'] = pTM2

        pCTM1 = request.form.get('pCTM1', None)
        if pCTM1: data0['pCTM1'] = pCTM1

        pCTM2 = request.form.get('pCTM2', None)
        if pCTM2: data0['pCTM2'] = pCTM2

        data = {'myae-params' : data0}
        for key, fields in data.items(): penv['rc'][0].hmset(key, fields)
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'shm/create/', methods=['POST', 'GET'])
@Util.time_me()
def action_create_shm():
    """创建shm"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        field_is_valid = False
        shm_size = request.form.get('shm_size', None)
        if shm_size:
            if isinstance(shm_size, str) and shm_size.isdigit():
                shm_size = int(shm_size)
                if shm_size > 0:
                    field_is_valid = True
            if isinstance(shm_size, int) and shm_size > 0:
                    field_is_valid = True
        if not field_is_valid:
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': 'shm_size字段非法',}), 200)

        total_size = 0
        for _, shm in penv['sysv_shm'].items():
            total_size += shm['shm_obj'].size
        if total_size+shm_size > penv['sysv_shm_valve']:
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': 'shm超过1GB配额',}), 200)

        field_is_valid = False
        shm_key = request.form.get('shm_key', None)
        if shm_key is None:
            shm_key = struct.unpack('I', os.urandom(4))[0]
            field_is_valid = True
        elif isinstance(shm_key, int) and shm_key>0:
            field_is_valid = True
        elif isinstance(shm_key, str):
            if shm_key.startswith('0x') and all(i in "0123456789abcdefABCDEF" for i in shm_key[2:]):
                shm_key = int(shm_key, 16)
            elif shm_key.isdigit():
                shm_key = int(shm_key)
            if isinstance(shm_key, int) and shm_key>0:
                field_is_valid = True
        if not field_is_valid:
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': 'shm_key字段非法',}), 200)

        shm_obj = sysv_ipc.SharedMemory(shm_key, flags=sysv_ipc.IPC_CREAT, mode=0o666, size=shm_size)
        shm_obj.detach()
        penv['sysv_shm'][f'{shm_key}'] = {
            'shm_key' : shm_key, #生成的key，Python端用
            'shm_obj' : shm_obj,
            'shm_id'  : shm_obj.id, #生成的shmid，C端用
        }

        print(f"shm创建成功=> key:[{shm_key}], shmid:[{shm_obj.id}]")
        return make_response(jsonify({'code': 0, 'data':f"shm_key:{hex(shm_key)},shm_id:{shm_obj.id}", 'msg': 'ok',}), 200)
    except (Exception) as e:
        emsg = f"shm创建异常【{exinfo()}】\n"
        print(emsg)
        return make_response(jsonify({'code': 1001, 'data': '', 'msg': emsg,}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'shm/del/', methods=['POST', 'GET'])
@Util.time_me()
def action_del_shm():
    """删除shm"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        shm_key = request.form.get('shm_key', None)
        if not shm_key:
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': 'shm_key字段非法',}), 200)
        if isinstance(shm_key, int):
            shm_key = str(shm_key)
        if isinstance(shm_key, str):
            if shm_key.startswith('0x') and all(i in "0123456789abcdefABCDEF" for i in shm_key[2:]):
                shm_key = str(int(shm_key, 16))

        if shm_key not in penv['sysv_shm']:
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': f'shm_key:[{shm_key}]无效',}), 200)

        shm = penv['sysv_shm'][shm_key]['shm_obj']
        shmid = shm.id
        shm.remove()
        penv['sysv_shm'].pop(shm_key)

        print(f"shm删除成功=> key:[{shm_key}], shmid:[{shmid}]")
        return make_response(jsonify({'code': 0, 'data': '', 'msg': 'ok',}), 200)
    except (Exception) as e:
        emsg = f"shm删除异常【{exinfo()}】\n"
        print(emsg)
        return make_response(jsonify({'code': 1001, 'data': '', 'msg': emsg,}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'firmwares/create/', methods=['POST', 'GET'])
@Util.time_me()
def action_create():
    """增加固件"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        firm_name = request.form.get('firm_name', None)
        brand = request.form.get('brand', None)

        if not isinstance(firm_name, str):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': 'firm_name字段非法',}), 200)
        if not isinstance(brand, str):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': 'brand字段非法',}), 200)

        firm_full_name = f"{penv['upload_dir']}/{firm_name}"
        if not (os.path.exists(firm_full_name) and os.path.isfile(firm_full_name)):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': '该固件尚未上传',}), 200)

        firm_full_name = f"{penv['work_dir']}/{firm_name}"
        if os.path.exists(firm_full_name) and os.path.isfile(firm_full_name):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': '该固件已增加',}), 200)

        rc = penv['rc'][0]
        firm_md5 = Util.gen_md5(firm_name.encode('utf8'))
        if rc.exists(firm_md5):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': '该固件MD5重复',}), 200)

        rc.hmset(firm_md5, {'firm_name':firm_name, 'brand':brand, })
        rc.sadd(penv['firmwares'], firm_md5)
        rc.bgsave()
        mycmd(r"ln {0}/{1} {2}/{1}".format(penv['upload_dir'], firm_name, penv['work_dir']))
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'firmwares/del/', methods=['POST', 'GET'])
@Util.time_me()
def action_del():
    """删除固件"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        firm_name = request.form.get('firm_name', None)
        if firm_name:
            return __action_del_impl(firm_name)
        else:
            for root, dirs, files in os.walk(penv['work_dir'], topdown=True, onerror=None, followlinks=False):
                for i in files:
                    if i == 'README.md':
                        continue
                    __action_del_impl2(i, Util.gen_md5(i.encode('utf8')))
                break
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['rc'][0].bgsave()
        penv['apirunning'] = False


def __action_del_impl(firm_name):
    if not isinstance(firm_name, str):
        return make_response(jsonify({'code': 1001, 'data': '', 'msg': 'firm_name字段非法',}), 200)

    firm_full_name = f"{penv['work_dir']}/{firm_name}"
    if not (os.path.exists(firm_full_name) and os.path.isfile(firm_full_name)):
        return make_response(jsonify({'code': 1001, 'data': '', 'msg': '该固件不存在',}), 200)

    firm_md5 = Util.gen_md5(firm_name.encode('utf8'))
    if not penv['rc'][0].exists(firm_md5):
        return make_response(jsonify({'code': 1001, 'data': '', 'msg': '该固件MD5不存在',}), 200)

    __action_del_impl2(firm_name, firm_md5)
    return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)


def __action_del_impl2(firm_name, firm_md5):
    rc = penv['rc'][0]
    rc.delete(firm_md5)
    rc.srem(penv['firmwares'], firm_md5)
    mycmd(r"rm -fr {1}/{0}".format(firm_name, penv['work_dir']))


@app.route(penv['url_prefix']+'firmwares/list/', methods=['POST', 'GET'])
@Util.time_me()
def action_query():
    """查询固件列表"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        rc = penv['rc'][0]
        firmwares = rc.smembers(penv['firmwares'])
        data = [rc.hgetall(i) for i in firmwares]
        return make_response(jsonify({'code': 1, 'data': str(data), 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'firmwares/qbrand/', methods=['POST', 'GET'])
@Util.time_me()
def action_qbrand():
    """查询固件品牌"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        firm_name = request.form.get('firm_name', None)

        if not isinstance(firm_name, str):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': 'firm_name字段非法',}), 200)

        firm_md5 = Util.gen_md5(firm_name.encode('utf8'))
        brand = penv['rc'][0].hget(firm_md5, 'brand')

        return make_response(jsonify({'code': 1, 'data': str(brand, encoding='utf-8'), 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'engine/start/', methods=['POST', 'GET'])
@Util.time_me()
def action_start():
    """启动引擎"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        base_dir = penv['upload_dir'][: penv['upload_dir'].rfind(r"/")]
        msg = f"PLS在终端执行命令=> cd {base_dir}; sudo ./myaeer 2>&1 |ts |tee ./logs/andygood.log"
        return make_response(jsonify({'code': 1, 'data': '', 'msg': msg,}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'register/', methods=['POST', 'GET'])
@Util.time_me()
def action_register():
    """注册引擎"""
    penv['processid'] = request.form.get('processid', None)
    return make_response(jsonify({'code': 1, 'data': str(penv['processid']), 'msg': 'ok',}), 200)


@app.route(penv['url_prefix']+'engine/stop/', methods=['POST', 'GET'])
@Util.time_me()
def action_stop():
    """停止引擎"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        if not penv['processid']:
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': '引擎尚未启动',}), 200)

        iid, processid = penv['processid'].split('@')
        mycmd(r'echo -e "\nq\n" | sudo /usr/bin/nc -U /tmp/qemu.{0}'.format(iid))
        mycmd(r'sudo kill -TERM -{0}'.format(processid))
        print("引擎停止，进程ID【{0}】\n".format(processid))
        penv['processid'] = None
        return make_response(jsonify({'code': 1, 'data': str(processid), 'msg': 'ok',}), 200)
    except (Exception) as e:
        emsg = f"引擎停止异常【{exinfo()}】\n"
        print(emsg)
        return make_response(jsonify({'code': 1001, 'data': '', 'msg': emsg,}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'engine/clean/', methods=['POST', 'GET'])
@Util.time_me()
def action_clean():
    """清理引擎"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        if penv['processid']:
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': '引擎尚未停止，不能CLEAN',}), 200)

        base_dir = penv['upload_dir'][: penv['upload_dir'].rfind(r"/")]
        mycmd(r"cd {0} && sudo ./myaeer --clean".format(base_dir))
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error':'Not Found'}), 404)

####################################################################################################
if __name__=='__main__':
    rcp = redis.ConnectionPool(host='localhost', port=5168, password=None, max_connections=168)
    rcc = redis.Redis(connection_pool = rcp)
    if not rcc.ping():
        raise Exception('Redis PING操作异常！')
    penv['rc'] = [rcc, rcp]

    tmp = '\n'.join([str(i) for i in app.url_map.iter_rules()])
    print(f'\n接口清单：\n{tmp}')
    app.run(port=5368, host='0.0.0.0', debug=False)

    for _,shm in penv['sysv_shm'].items():
        shm['shm_obj'].remove()

    penv['rc'][0].save()
    penv['rc'][0].close()
    penv['rc'][1].disconnect(inuse_connections=True)
