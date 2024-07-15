#!/usr/bin/env python3
#coding=utf-8

"""
    Created on: 2024-07-15 by AndyZhou
"""

import os, logging, json, redis
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
}
logging.getLogger('werkzeug').setLevel(logging.ERROR)


@app.route(penv['url_prefix']+'create/', methods=['POST', 'GET'])
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

        firm_full_name = "{0}/{1}".format(penv['upload_dir'], firm_name)
        if not (os.path.exists(firm_full_name) and os.path.isfile(firm_full_name)):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': '该固件尚未上传',}), 200)

        firm_full_name = "{0}/{1}".format(penv['work_dir'], firm_name)
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


@app.route(penv['url_prefix']+'del/', methods=['POST', 'GET'])
@Util.time_me()
def action_del():
    """删除固件"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        firm_name = request.form.get('firm_name', None)

        if not isinstance(firm_name, str):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': 'firm_name字段非法',}), 200)

        firm_full_name = "{0}/{1}".format(penv['work_dir'], firm_name)
        if not (os.path.exists(firm_full_name) and os.path.isfile(firm_full_name)):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': '该固件不存在',}), 200)

        rc = penv['rc'][0]
        firm_md5 = Util.gen_md5(firm_name.encode('utf8'))
        if not rc.exists(firm_md5):
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': '该固件MD5不存在',}), 200)

        rc.delete(firm_md5)
        rc.srem(penv['firmwares'], firm_md5)
        rc.bgsave()
        mycmd(r"rm -fr {1}/{0}".format(firm_name, penv['work_dir']))
        return make_response(jsonify({'code': 1, 'data': '', 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'query/', methods=['POST', 'GET'])
@Util.time_me()
def action_query():
    """查询固件列表"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        rc = penv['rc'][0]
        firmwares = rc.smembers(penv['firmwares'])
        data = []
        for i in firmwares:
            data.append(rc.hgetall(i))

        return make_response(jsonify({'code': 1, 'data': str(data), 'msg': 'ok',}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'qbrand/', methods=['POST', 'GET'])
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


@app.route(penv['url_prefix']+'start/', methods=['POST', 'GET'])
@Util.time_me()
def action_start():
    """启动引擎"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        if penv['processid'] is not None:
            return make_response(jsonify({'code': 1001, 'data': '', 'msg': '引擎禁止多开',}), 200)

        base_dir = penv['upload_dir']
        base_dir = base_dir[: base_dir.rfind(r"/")]
        msg = "cd {0}; sudo ./myaeer 2>&1 |ts '[%Y-%m-%d %H:%M:%S]' > ./share/andygood.log".format(base_dir)
        msg = "PLS在终端执行命令=> {0}".format(msg)
        return make_response(jsonify({'code': 1, 'data': '', 'msg': msg,}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'register/', methods=['POST', 'GET'])
@Util.time_me()
def action_register():
    """注册引擎"""
    penv['processid'] = request.form.get('processid', None)
    return make_response(jsonify({'code': 1, 'data': str(penv['processid']), 'msg': 'ok',}), 200)


@app.route(penv['url_prefix']+'stop/', methods=['POST', 'GET'])
@Util.time_me()
def action_stop():
    """停止引擎"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        processid = penv['processid']
        mycmd(r"sudo kill -TERM -{0}".format(processid))
        print("引擎停止，进程ID【{0}】\n".format(processid))
        penv['processid'] = None
        return make_response(jsonify({'code': 1, 'data': str(processid), 'msg': 'ok',}), 200)
    except (Exception) as e:
        emsg = "引擎停止异常【{}】\n".format(exinfo())
        print(emsg)
        return make_response(jsonify({'code': 1001, 'data': '', 'msg': emsg,}), 200)
    finally:
        penv['apirunning'] = False


@app.route(penv['url_prefix']+'clean/', methods=['POST', 'GET'])
@Util.time_me()
def action_clean():
    """清理引擎"""
    if penv['apirunning']:
        return make_response(jsonify({'code': 1003, 'data': '', 'msg': '接口执行中',}), 200)
    penv['apirunning'] = True

    try:
        base_dir = penv['upload_dir']
        base_dir = base_dir[: base_dir.rfind(r"/")]
        mycmd(r"sudo {0}/myaeer --clean".format(base_dir))
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

    app.run(port=5368, host='0.0.0.0', debug=False)

    penv['rc'][0].close()
    penv['rc'][1].disconnect(inuse_connections=True)
