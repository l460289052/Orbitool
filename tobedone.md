+ 把Main.py和utils合并，添加清除临时文件功能
+ 使用pool写process，并且想办法增加进程中止功能
+ 增加类似property实现方法的的函数。例如

```python
class Widget(...):
    @threadBegin
    def some_process_1(self, ...):
        pass
    @some_process_1.end
    def some_process_1(self, ...):
        pass
        
    @busy
    def some_process_2(self, ...):
        pass

    @some_process_2.except
    def some_process_2(self, ...):
        pass
```
+ Datatable增加按类操作。例如按行操作就给一个实例，按列操作就……