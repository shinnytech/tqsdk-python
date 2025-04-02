from PyInstaller.utils.hooks import collect_data_files, collect_submodules
datas = collect_data_files('tqsdk', includes=['web', 'expired_quotes.json.lzma'])
hiddenimports = collect_submodules('tqsdk_ctpse')
