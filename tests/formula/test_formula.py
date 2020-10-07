from utils.formula import Formula, FormulaHint
import threading

def test_formula1():
    s = "N[15]O3-"
    f: FormulaHint = Formula(s)
    assert f['O'] == 3
    assert f['N[15]'] == 1
    assert f['N'] == 1
    assert f.charge == -1


def formula2():
    'O[18]3O0C7H[2]0H2'
    f: FormulaHint = Formula()
    f.addElement('O',18,3)
    f.addElement('O',0,0)
    f.addElement('C',0,7)
    f.addElement('H',2,0)
    f.addElement('H',0,2)

def test_formula2():
    '''
    用thread不顶用的，大家都在等这个线程退出，我也不知道它该怎么退出，唉
    '''
    thread = threading.Thread(target=formula2)
    thread.start()
    thread.join(timeout=0.1)
    assert not thread.is_alive()
    thread._stop()
    del thread

