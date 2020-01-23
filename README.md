## Что это
Данная библиотека служит для быстрого написания фоновых приложений и системных служб.
В нем имеются логирование, сохранение локальных файлов, контроль состояния потоков и используемой памяти, способность к самообновлению (например из github) и контроль запуска одного процесса.

## Быстрый старт
```python
from mypylib import *

local = MyPyClass()

def Config():
	local.db["config"]["isStartOnlyOneProcess"] = False
#end define

def General():
	while True:
		local.PrintSelfTestingResult()
		time.sleep(3)
#end define

###
### Start of the program
###

if __name__ == "__main__":
	Config()
	local.Init()
	General()
```