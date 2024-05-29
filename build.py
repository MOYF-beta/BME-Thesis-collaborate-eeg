from setuptools import setup
import py2exe

setup(
    name='collaboration-measurement',
    console=['game_frontend.py'],  # 指定主脚本文件
    version='1.0',
    py_modules=[
        'game_backend', 
        'game_strategy', 
        'net_config', 
        'tetris_shape', 
        'twisted_network_protocol'
    ], 
    options={
        'py2exe': {
            'bundle_files': 3,
            'compressed': True,
        }
    },
    zipfile=None,
    data_files=[
        ('.', ['rect']),
    ],
)
