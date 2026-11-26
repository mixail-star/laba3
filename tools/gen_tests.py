"""Генерирует три набора юнит-тестов (Boost.Test, Google Test, Catch2) из одного описания.

Строки внутри теста:
  EQ(a, b)            - равенство
  TRUE(x) / FALSE(x)  - условие
  THROWS(expr, Type)  - ожидается исключение Type
  NOTHROW(expr)       - исключения быть не должно
Остальные строки переносятся как есть (обычный C++).
"""
import re
import sys
from pathlib import Path

TESTS = {}


def test(suite, name, body):
    TESTS.setdefault(suite, []).append((name, None, body.strip("\n")))


# Параметризованный тест: одно тело выполняется для каждого значения param из выражения cases
def ptest(suite, name, param_type, cases, body):
    TESTS.setdefault(suite, []).append((name, (param_type, cases), body.strip("\n")))


# ---------------------------------------------------------------- Array
test("ArrayTests", "PushBackAndGet", """
Array a;
TRUE(a.empty())
for (const char* v : {"10", "20", "30", "40", "50"}) a.push_back(v);
EQ(a.length(), 5)
std::string v;
TRUE(a.get(0, v))
EQ(v, "10")
EQ(a.at(4), "50")
FALSE(a.get(5, v))
FALSE(a.get(-1, v))
FALSE(a.empty())
EQ(a.type_name(), "Array")
""")
test("ArrayTests", "InsertAtBeginMiddleEnd", """
Array a;
TRUE(a.insert(0, "b"))
TRUE(a.insert(0, "a"))
TRUE(a.insert(2, "d"))
TRUE(a.insert(2, "c"))
EQ(join(a), "a b c d")
FALSE(a.insert(-1, "x"))
FALSE(a.insert(5, "x"))
EQ(a.length(), 4)
""")
test("ArrayTests", "SetAndErase", """
Array a;
for (const char* v : {"1", "2", "3", "4"}) a.push_back(v);
TRUE(a.set(0, "one"))
FALSE(a.set(4, "z"))
FALSE(a.set(-1, "z"))
std::string removed;
TRUE(a.erase(1, removed))
EQ(removed, "2")
EQ(join(a), "one 3 4")
TRUE(a.erase(2, removed))
EQ(removed, "4")
FALSE(a.erase(2, removed))
FALSE(a.erase(-1, removed))
EQ(a.length(), 2)
""")
test("ArrayTests", "CopyMoveClearAndGrow", """
Array a;
for (int i = 0; i < 1000; i++) a.push_back(std::to_string(i));
EQ(a.length(), 1000)
EQ(a.at(999), "999")
Array copy(a);
copy.set(0, "changed");
EQ(a.at(0), "0")
Array assigned;
assigned = copy;
EQ(assigned.at(0), "changed")
Array& self = assigned;
assigned = self;
EQ(assigned.length(), 1000)
Array moved(std::move(copy));
EQ(moved.at(0), "changed")
copy.push_back("reused");
EQ(join(copy), "reused")
Array target;
target = std::move(moved);
EQ(target.length(), 1000)
moved.push_back("again");
EQ(moved.length(), 1)
a.clear();
TRUE(a.empty())
a.push_back("again");
EQ(join(a), "again")
EQ(join(a.values()), "again")
""")

# ---------------------------------------------------------------- SinglyList
test("SinglyListTests", "PushFrontBack", """
SinglyList l;
std::string v;
FALSE(l.front(v))
l.push_back("b");
l.push_front("a");
l.push_back("c");
EQ(join(l), "a b c")
TRUE(l.front(v))
EQ(v, "a")
EQ(l.length(), 3)
EQ(l.type_name(), "SinglyList")
SinglyList one;
one.push_front("only");
EQ(join(one), "only")
""")
test("SinglyListTests", "InsertAfterBefore", """
SinglyList l;
FALSE(l.insert_before("x", "y"))
FALSE(l.insert_after("x", "y"))
l.push_back("a");
l.push_back("c");
TRUE(l.insert_after("a", "b"))
TRUE(l.insert_after("c", "d"))
TRUE(l.insert_before("a", "start"))
TRUE(l.insert_before("d", "c2"))
FALSE(l.insert_after("missing", "x"))
FALSE(l.insert_before("missing", "x"))
EQ(join(l), "start a b c c2 d")
l.push_back("tail");
EQ(join(l), "start a b c c2 d tail")
""")
test("SinglyListTests", "PopFrontBack", """
SinglyList l;
for (const char* v : {"1", "2", "3"}) l.push_back(v);
std::string v;
TRUE(l.pop_front(v))
EQ(v, "1")
TRUE(l.pop_back(v))
EQ(v, "3")
TRUE(l.pop_back(v))
EQ(v, "2")
TRUE(l.empty())
FALSE(l.pop_front(v))
FALSE(l.pop_back(v))
l.push_back("x");
TRUE(l.pop_front(v))
TRUE(l.empty())
l.push_back("y");
EQ(join(l), "y")
""")
test("SinglyListTests", "RemoveContainsGetClear", """
SinglyList l;
FALSE(l.remove("a"))
for (const char* v : {"a", "b", "c", "d"}) l.push_back(v);
TRUE(l.remove("a"))
TRUE(l.remove("d"))
TRUE(l.remove("c"))
FALSE(l.remove("zzz"))
TRUE(l.contains("b"))
FALSE(l.contains("a"))
std::string v;
TRUE(l.get(0, v))
EQ(v, "b")
FALSE(l.get(1, v))
FALSE(l.get(-1, v))
l.push_back("e");
EQ(join(l), "b e")
l.clear();
TRUE(l.empty())
l.push_front("z");
EQ(join(l), "z")
""")

# ---------------------------------------------------------------- DoublyList
test("DoublyListTests", "PushAndValues", """
DoublyList l;
l.push_back("b");
l.push_front("a");
l.push_back("c");
EQ(join(l), "a b c")
EQ(l.type_name(), "DoublyList")
DoublyList front_only;
front_only.push_front("2");
front_only.push_front("1");
EQ(join(front_only), "1 2")
""")
test("DoublyListTests", "InsertAfterBefore", """
DoublyList l;
FALSE(l.insert_after("x", "y"))
FALSE(l.insert_before("x", "y"))
l.push_back("b");
TRUE(l.insert_before("b", "a"))
TRUE(l.insert_after("b", "d"))
TRUE(l.insert_after("b", "c"))
TRUE(l.insert_before("d", "c2"))
TRUE(l.insert_after("d", "e"))
EQ(join(l), "a b c c2 d e")
std::string v;
TRUE(l.pop_back(v))
EQ(v, "e")
TRUE(l.pop_front(v))
EQ(v, "a")
""")
test("DoublyListTests", "PopRemoveGet", """
DoublyList l;
std::string v;
FALSE(l.pop_front(v))
FALSE(l.pop_back(v))
for (const char* s : {"1", "2", "3", "4", "5"}) l.push_back(s);
TRUE(l.pop_front(v))
EQ(v, "1")
TRUE(l.pop_back(v))
EQ(v, "5")
TRUE(l.remove("3"))
FALSE(l.remove("3"))
TRUE(l.contains("2"))
FALSE(l.contains("9"))
TRUE(l.get(1, v))
EQ(v, "4")
FALSE(l.get(2, v))
FALSE(l.get(-1, v))
TRUE(l.remove("2"))
TRUE(l.remove("4"))
TRUE(l.empty())
l.push_back("x");
TRUE(l.pop_back(v))
TRUE(l.empty())
l.push_back("y");
TRUE(l.pop_front(v))
TRUE(l.empty())
""")
test("DoublyListTests", "Clear", """
DoublyList l;
for (const char* v : {"x", "y", "z"}) l.push_back(v);
l.clear();
TRUE(l.empty())
EQ(join(l), "")
l.push_back("again");
EQ(l.length(), 1)
""")

# ---------------------------------------------------------------- Stack / Queue
test("StackQueueTests", "StackIsLifo", """
Stack s;
std::string v;
FALSE(s.pop(v))
FALSE(s.top(v))
for (const char* x : {"1", "2", "3"}) s.push(x);
TRUE(s.top(v))
EQ(v, "3")
EQ(join(s), "3 2 1")
TRUE(s.pop(v))
EQ(v, "3")
TRUE(s.pop(v))
EQ(v, "2")
EQ(s.length(), 1)
EQ(s.type_name(), "Stack")
s.clear();
TRUE(s.empty())
""")
test("StackQueueTests", "QueueIsFifo", """
Queue q;
std::string v;
FALSE(q.pop(v))
FALSE(q.front(v))
for (const char* x : {"a", "b", "c"}) q.push(x);
TRUE(q.front(v))
EQ(v, "a")
TRUE(q.pop(v))
EQ(v, "a")
q.push("d");
EQ(join(q), "b c d")
EQ(q.length(), 3)
EQ(q.type_name(), "Queue")
q.clear();
TRUE(q.empty())
""")

# ---------------------------------------------------------------- RBTree
test("RBTreeTests", "InsertBalancesLikeLab1", """
RBTree t;
for (const char* v : {"10", "20", "30", "15", "5", "25"}) {
    TRUE(t.insert(v))
}
FALSE(t.insert("15"))
EQ(join(t.preorder()), "20(B) 10(B) 5(R) 15(R) 30(B) 25(R)")
EQ(join(t.inorder()), "5(R) 10(B) 15(R) 20(B) 25(R) 30(B)")
EQ(join(t.postorder()), "5(R) 15(R) 10(B) 25(R) 30(B) 20(B)")
EQ(join(t.bfs()), "20(B) 10(B) 30(B) 5(R) 15(R) 25(R)")
EQ(join(t.keys()), "5 10 15 20 25 30")
EQ(join(t), "5 10 15 20 25 30")
TRUE(t.is_valid())
EQ(t.length(), 6)
EQ(t.type_name(), "RBTree")
""")
test("RBTreeTests", "SearchMinMaxNextPrev", """
RBTree t;
std::string v;
FALSE(t.min_key(v))
FALSE(t.max_key(v))
for (const char* s : {"10", "20", "30", "15", "5", "25"}) t.insert(s);
TRUE(t.contains("25"))
FALSE(t.contains("99"))
TRUE(t.min_key(v))
EQ(v, "5")
TRUE(t.max_key(v))
EQ(v, "30")
TRUE(t.next("15", v))
EQ(v, "20")
TRUE(t.next("20", v))
EQ(v, "25")
TRUE(t.prev("15", v))
EQ(v, "10")
TRUE(t.prev("20", v))
EQ(v, "15")
TRUE(t.prev("25", v))
EQ(v, "20")
FALSE(t.next("30", v))
FALSE(t.prev("5", v))
FALSE(t.next("99", v))
FALSE(t.prev("99", v))
""")
test("RBTreeTests", "EraseAllCases", """
RBTree t;
FALSE(t.erase("1"))
for (const char* v : {"10", "20", "30", "15", "5", "25"}) t.insert(v);
TRUE(t.erase("20"))
EQ(join(t.preorder()), "25(B) 10(B) 5(R) 15(R) 30(B)")
TRUE(t.erase("10"))
EQ(join(t.preorder()), "25(B) 15(B) 5(R) 30(B)")
FALSE(t.erase("99"))
TRUE(t.erase("5"))
TRUE(t.erase("30"))
TRUE(t.erase("25"))
TRUE(t.erase("15"))
TRUE(t.empty())
TRUE(t.is_valid())
""")
test("RBTreeTests", "StaysValidUnderRandomOps", """
RBTree t;
unsigned x = 12345;
int inserted = 0;
for (int i = 0; i < 3000; i++) {
    x = x * 1103515245U + 12345U;
    std::string key = std::to_string((x >> 8) % 500);
    if ((x >> 4) % 3 == 0) t.erase(key); else inserted += t.insert(key) ? 1 : 0;
}
TRUE(inserted > 0)
TRUE(t.is_valid())
""")
test("RBTreeTests", "OrderingAndDiagram", """
RBTree t;
EQ(t.diagram(), "(empty tree)\\n")
EQ(join(t.bfs()), "")
for (const char* v : {"2", "10", "-5", "abc", "99"}) t.insert(v);
EQ(join(t.keys()), "-5 2 10 99 abc")
RBTree d;
for (const char* v : {"2", "1", "3", "4"}) d.insert(v);
EQ(d.diagram(), "2(B)\\n|-- L: 1(B)\\n`-- R: 3(B)\\n    `-- R: 4(R)\\n")
RBTree left;
for (const char* v : {"3", "2", "1", "0"}) left.insert(v);
EQ(left.diagram(), "2(B)\\n|-- L: 1(B)\\n|   `-- L: 0(R)\\n`-- R: 3(B)\\n")
left.clear();
TRUE(left.empty())
TRUE(left.insert("z"))
TRUE(left.contains("z"))
""")

# ---------------------------------------------------------------- Hash tables
test("HashTableTests", "HashFunction", """
EQ(hash_string(""), 0U)
EQ(hash_string("a"), 97U)
EQ(hash_string("ab"), 97U * 31U + 98U)
TRUE(hash_string("ab") != hash_string("ba"))
""")
ptest("HashTableTests", "PutGetRemove", "TableKind", "table_kinds()", """
auto t = param.make();
TRUE(t->empty())
FALSE(t->get("x").has_value())
FALSE(t->remove("x"))
TRUE(t->put("apple", "1"))
TRUE(t->put("pear", "2"))
FALSE(t->put("apple", "10"))
EQ(t->get("apple").value_or("-"), "10")
TRUE(t->contains("pear"))
FALSE(t->contains("plum"))
EQ(t->length(), 2)
TRUE(t->load_factor() > 0.0)
TRUE(t->remove("pear"))
FALSE(t->remove("pear"))
FALSE(t->contains("pear"))
EQ(pairs(*t), "apple=10")
t->clear();
TRUE(t->empty())
TRUE(t->put("after", "clear"))
""")
ptest("HashTableTests", "GrowsAndKeepsAllKeys", "TableKind", "table_kinds()", """
auto t = param.make();
const int start = t->capacity();
for (int i = 0; i < 2000; i++) t->put("key" + std::to_string(i), std::to_string(i));
EQ(t->length(), 2000)
TRUE(t->capacity() > start)
TRUE(t->load_factor() <= 0.75)
bool all = true;
for (int i = 0; i < 2000; i++) all = all && t->get("key" + std::to_string(i)).value_or("") == std::to_string(i);
TRUE(all)
for (int i = 0; i < 2000; i += 2) t->remove("key" + std::to_string(i));
EQ(t->length(), 1000)
FALSE(t->contains("key0"))
TRUE(t->contains("key1"))
""")
test("HashTableTests", "ChainSpecifics", """
ChainHashTable t(4);
EQ(t.capacity(), 4)
EQ(t.type_name(), "ChainHashTable")
for (const char* k : {"a", "b", "c", "d", "e"}) t.put(k, k);
TRUE(t.capacity() >= 8)
TRUE(t.longest_chain() >= 1)
ChainHashTable zero(0);
EQ(zero.capacity(), 8)
ChainHashTable copy(t);
copy.put("f", "f");
EQ(t.length(), 5)
ChainHashTable assigned;
assigned = copy;
ChainHashTable& self = assigned;
assigned = self;
EQ(assigned.length(), 6)
ChainHashTable moved(std::move(assigned));
EQ(moved.get("f").value_or("-"), "f")
FALSE(assigned.get("f").has_value())
FALSE(assigned.remove("f"))
TRUE(assigned.put("x", "1"))
ChainHashTable target;
target = std::move(moved);
EQ(target.length(), 6)
""")
test("HashTableTests", "OpenAddressingTombstones", """
OpenHashTable lin(OpenHashTable::Probing::Linear, 11);
OpenHashTable dbl(OpenHashTable::Probing::Double, 11);
EQ(lin.type_name(), "OpenHashTable/linear")
EQ(dbl.type_name(), "OpenHashTable/double")
TRUE(lin.probing() == OpenHashTable::Probing::Linear)
for (OpenHashTable* t : {&lin, &dbl}) {
    for (const char* k : {"pear", "lime", "grape"}) t->put(k, k);
    EQ(t->capacity(), 11)
    TRUE(t->probes("grape") >= 2)
    TRUE(t->remove("lime"))
    EQ(t->get("grape").value_or("-"), "grape")
    TRUE(t->put("lime", "again"))
    EQ(t->get("lime").value_or("-"), "again")
    TRUE(t->probes("missing") >= 1)
}
EQ(lin.probes("grape"), 3)
EQ(dbl.probes("grape"), 2)
""")
test("HashTableTests", "OpenHelpersAndCopies", """
TRUE(OpenHashTable::is_prime(2))
TRUE(OpenHashTable::is_prime(1009))
FALSE(OpenHashTable::is_prime(1))
FALSE(OpenHashTable::is_prime(1000))
EQ(OpenHashTable::next_prime(1000), 1009)
OpenHashTable small(OpenHashTable::Probing::Linear, 1);
EQ(small.capacity(), 3)
OpenHashTable t(OpenHashTable::Probing::Double, 11);
for (int i = 0; i < 30; i++) {
    t.put("k" + std::to_string(i), "v");
    t.remove("k" + std::to_string(i));
}
EQ(t.length(), 0)
TRUE(t.put("alive", "1"))
OpenHashTable copy(t);
copy.put("other", "2");
EQ(t.length(), 1)
OpenHashTable assigned;
assigned = copy;
OpenHashTable& self = assigned;
assigned = self;
EQ(assigned.length(), 2)
OpenHashTable moved(std::move(assigned));
EQ(moved.get("other").value_or("-"), "2")
FALSE(assigned.get("other").has_value())
FALSE(assigned.remove("other"))
EQ(assigned.probes("other"), 0)
TRUE(assigned.put("x", "1"))
OpenHashTable target;
target = std::move(moved);
EQ(target.length(), 2)
""")

# ---------------------------------------------------------------- Serialization
# Одна проверка для всех 9 контейнеров и обоих форматов (18 запусков)
ptest("SerializationTests", "Roundtrip", "FormatSample", "format_samples()", """
auto original = param.sample.make_filled();
std::stringstream buffer;
original->save(buffer, param.format);
auto loaded = param.sample.make_empty();
loaded->load(buffer, param.format);
EQ(loaded->type_name(), original->type_name())
EQ(loaded->length(), original->length())
EQ(describe(*loaded), describe(*original))
""")
# Пустой контейнер любого типа сохраняется как {"Тип": []} и загружается обратно
ptest("SerializationTests", "EmptyContainer", "Sample", "samples()", """
auto c = param.make_empty();
TRUE(c->empty())
std::stringstream out;
c->save(out, Format::Text);
EQ(out.str(), "{\\n  \\"" + c->type_name() + "\\": []\\n}\\n")
c->load(out, Format::Text);
EQ(c->length(), 0)
""")
# Повреждённый JSON отклоняется, старое содержимое не меняется
ptest("SerializationTests", "RejectsBadJson", "std::string", """std::vector<std::string>{
    "", "[]", "{}", "{\\"Array\\": [\\"\\\\ud800\\"]}", "{\\"Array\\": [\\"1\\"", "{\\"Array\\": [\\"1\\" \\"2\\"]}",
    "{\\"Array\\" [\\"1\\"]}", "{\\"Array\\": [\\"bad\\\\q\\"]}", "{\\"Array\\": [\\"\\\\u12\\"]}",
    "{\\"Array\\": [\\"open", "{\\"Queue\\": [\\"x\\"]}", "{\\"Array\\": [], \\"Queue\\": []}",
    "{\\"Array\\": []} tail"}""", """
Array a;
a.push_back("old");
std::stringstream in(param);
THROWS(a.load(in, Format::Text), std::runtime_error)
EQ(join(a), "old")
""")
# Неверные метки дерева отклоняются, дерево остаётся прежним
ptest("SerializationTests", "RejectsBadTree", "std::string", """std::vector<std::string>{
    "{\\"RBTree\\": [\\"5(X)\\"]}", "{\\"RBTree\\": [\\"5\\"]}", "{\\"RBTree\\": [\\"5(R)\\"]}",
    "{\\"RBTree\\": [\\"5(B)\\", \\"5(R)\\"]}", "{\\"RBTree\\": [\\"5(B)\\", \\"3(B)\\"]}"}""", """
RBTree t;
std::stringstream good("{\\"RBTree\\": [\\"5(B)\\", \\"3(R)\\", \\"8(R)\\"]}");
NOTHROW(t.load(good, Format::Text))
std::stringstream in(param);
THROWS(t.load(in, Format::Text), std::runtime_error)
EQ(join(t.preorder()), "5(B) 3(R) 8(R)")
""")
test("SerializationTests", "TextFormatIsLab1Json", """
SinglyList sl;
for (const char* v : {"a", "b"}) sl.push_back(v);
EQ(text_of(sl), "{\\n  \\"SinglyList\\": [\\"a\\", \\"b\\"]\\n}\\n")
RBTree t;
for (const char* v : {"10", "20", "30", "15", "5", "25"}) t.insert(v);
EQ(text_of(t), "{\\n  \\"RBTree\\": [\\"20(B)\\", \\"10(B)\\", \\"5(R)\\", \\"15(R)\\", \\"30(B)\\", \\"25(R)\\"]\\n}\\n")
ChainHashTable h;
h.put("k", "v");
EQ(text_of(h), "{\\n  \\"ChainHashTable\\": [\\"k\\", \\"v\\"]\\n}\\n")
Stack st;
for (const char* v : {"1", "2", "3"}) st.push(v);
Stack st2;
roundtrip(st, st2, Format::Text);
std::string v;
TRUE(st2.pop(v))
EQ(v, "3")
""")
test("SerializationTests", "JsonParsingLikeLab1", """
Array a;
std::stringstream spaced(" {  \\"Array\\" :\\n [ \\"1\\" ,\\t\\"2\\" ] } ");
NOTHROW(a.load(spaced, Format::Text))
EQ(join(a), "1 2")
std::stringstream numbers("{\\"Array\\": [15, -3]}");
NOTHROW(a.load(numbers, Format::Text))
EQ(join(a), "15 -3")
std::stringstream escapes("{\\"Array\\": [\\"a\\\\\\"b\\", \\"c\\\\\\\\d\\", \\"e\\\\nf\\", \\"\\\\t\\\\r\\\\/\\\\b\\\\f\\", \\"\\\\u0041\\\\u00e9\\\\u20ac\\"]}");
NOTHROW(a.load(escapes, Format::Text))
EQ(a.length(), 5)
EQ(a.at(0), "a\\"b")
EQ(a.at(1), "c\\\\d")
EQ(a.at(2), "e\\nf")
EQ(a.at(4), "A\\xc3\\xa9\\xe2\\x82\\xac")
Array ctrl;
ctrl.push_back(std::string(1, '\\x01'));
Array ctrl2;
roundtrip(ctrl, ctrl2, Format::Text);
EQ(ctrl2.at(0), std::string(1, '\\x01'))
""")
test("SerializationTests", "FilesRoundtrip", """
const std::string bin = "lab3_test_array.bin";
const std::string txt = "lab3_test_array.json";
Array a;
for (const char* v : {"1", "2", "3"}) a.push_back(v);
a.save_file(bin, Format::Binary);
a.save_file(txt, Format::Text);
Array b;
b.load_file(bin, Format::Binary);
EQ(join(b), "1 2 3")
Array c;
c.load_file(txt, Format::Text);
EQ(join(c), "1 2 3")
std::remove(bin.c_str());
std::remove(txt.c_str());
THROWS(c.load_file("no/such/dir/file.bin", Format::Binary), std::runtime_error)
THROWS(c.save_file("no/such/dir/file.bin", Format::Binary), std::runtime_error)
""")
test("SerializationTests", "RejectsBadBinary", """
Array a;
a.push_back("x");
std::stringstream bin;
a.save(bin, Format::Binary);
SinglyList wrong_type;
THROWS(wrong_type.load(bin, Format::Binary), std::runtime_error)
std::stringstream garbage("XXXXrest");
THROWS(a.load(garbage, Format::Binary), std::runtime_error)
std::string full;
{
    std::stringstream b2;
    a.save(b2, Format::Binary);
    full = b2.str();
}
std::stringstream truncated(full.substr(0, full.size() - 1));
THROWS(a.load(truncated, Format::Binary), std::runtime_error)
EQ(join(a), "x")
std::stringstream short_header(full.substr(0, 6));
THROWS(a.load(short_header, Format::Binary), std::runtime_error)
std::stringstream huge;
huge.write("L3B1", 4);
const char len_type[4] = {5, 0, 0, 0};
huge.write(len_type, 4);
huge.write("Array", 5);
const char one[4] = {1, 0, 0, 0};
huge.write(one, 4);
const char big[4] = {0, 0, 0, 0x7f};
huge.write(big, 4);
THROWS(a.load(huge, Format::Binary), std::runtime_error)
RBTree t;
t.insert("1");
t.insert("2");
std::stringstream tb;
t.save(tb, Format::Binary);
std::string data = tb.str();
std::stringstream cut(data.substr(0, data.size() - 2));
RBTree t2;
THROWS(t2.load(cut, Format::Binary), std::runtime_error)
TRUE(t2.empty())
ChainHashTable h;
std::stringstream odd("{\\"ChainHashTable\\": [\\"key\\"]}");
THROWS(h.load(odd, Format::Text), std::runtime_error)
""")


# ---------------------------------------------------------------- генерация

def split_args(s):
    depth, cur, out, in_str, esc = 0, "", [], False, False
    for ch in s:
        if in_str:
            cur += ch
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
            continue
        cur += ch
    out.append(cur.strip())
    return out


MACROS = {
    "gtest": {"EQ": "EXPECT_EQ({0}, {1});", "TRUE": "EXPECT_TRUE({0});", "FALSE": "EXPECT_FALSE({0});",
              "THROWS": "EXPECT_THROW({0}, {1});", "NOTHROW": "EXPECT_NO_THROW({0});"},
    "boost": {"EQ": "BOOST_CHECK_EQUAL({0}, {1});", "TRUE": "BOOST_CHECK({0});", "FALSE": "BOOST_CHECK(!({0}));",
              "THROWS": "BOOST_CHECK_THROW({0}, {1});", "NOTHROW": "BOOST_CHECK_NO_THROW({0});"},
    "catch2": {"EQ": "CHECK({0} == {1});", "TRUE": "CHECK({0});", "FALSE": "CHECK_FALSE({0});",
               "THROWS": "CHECK_THROWS_AS({0}, {1});", "NOTHROW": "CHECK_NOTHROW({0});"},
}
LINE = re.compile(r"^(\s*)(EQ|TRUE|FALSE|THROWS|NOTHROW)\((.*)\)\s*$")


def convert(body, fw):
    out = []
    for line in body.split("\n"):
        m = LINE.match(line)
        if m:
            indent, kind, args = m.groups()
            a = split_args(args)
            if fw == "catch2" and kind == "EQ":
                a = [f"({x})" if any(op in x for op in ("*", "+", "?")) else x for x in a]
            out.append(indent + MACROS[fw][kind].format(*a))
        else:
            out.append(line)
    return "\n".join("    " + l if l else l for l in out)


HEADER = '#include <cstdio>\n#include <sstream>\n#include <stdexcept>\n#include <string>\n#include <vector>\n#include "helpers.hpp"\n'


def gen_gtest():
    parts = ["#include <gtest/gtest.h>", HEADER]
    for suite, tests in TESTS.items():
        for name, param, body in tests:
            if param is None:
                parts.append(f"TEST({suite}, {name}) {{\n{convert(body, 'gtest')}\n}}\n")
                continue
            ptype, cases = param
            fixture = f"{suite}_{name}"
            parts.append(f"class {fixture} : public ::testing::TestWithParam<{ptype}> {{}};\n")
            parts.append(f"TEST_P({fixture}, Run) {{\n    const {ptype}& param = GetParam();\n{convert(body, 'gtest')}\n}}\n")
            parts.append(f"INSTANTIATE_TEST_SUITE_P({suite}, {fixture}, ::testing::ValuesIn({cases}));\n")
    return "\n".join(parts)


def gen_boost():
    parts = ["#define BOOST_TEST_MODULE lab3_boost", "#include <boost/test/unit_test.hpp>",
             "#include <boost/test/data/test_case.hpp>", "#include <boost/test/data/monomorphic.hpp>", HEADER]
    for suite, tests in TESTS.items():
        parts.append(f"BOOST_AUTO_TEST_SUITE({suite})\n")
        for name, param, body in tests:
            if param is None:
                parts.append(f"BOOST_AUTO_TEST_CASE({name}) {{\n{convert(body, 'boost')}\n}}\n")
                continue
            ptype, cases = param
            parts.append(f"BOOST_DATA_TEST_CASE({name}, boost::unit_test::data::make({cases}), param) {{\n"
                         f"{convert(body, 'boost')}\n}}\n")
        parts.append("BOOST_AUTO_TEST_SUITE_END()\n")
    return "\n".join(parts)


def gen_catch2():
    parts = ["#include <catch2/catch_test_macros.hpp>", "#include <catch2/generators/catch_generators.hpp>",
             "#include <catch2/generators/catch_generators_range.hpp>", HEADER]
    for suite, tests in TESTS.items():
        tag = suite.replace("Tests", "")
        for name, param, body in tests:
            head = ""
            if param is not None:
                ptype, cases = param
                head = f"    const {ptype} param = GENERATE(Catch::Generators::from_range({cases}));\n"
            parts.append(f'TEST_CASE("{name}", "[{tag}]") {{\n{head}{convert(body, "catch2")}\n}}\n')
    return "\n".join(parts)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    (out / "gtest_tests.cpp").write_text(gen_gtest())
    (out / "boost_tests.cpp").write_text(gen_boost())
    (out / "catch2_tests.cpp").write_text(gen_catch2())
    total = sum(len(v) for v in TESTS.values())
    param = sum(1 for v in TESTS.values() for t in v if t[1] is not None)
    print(f"suites: {len(TESTS)}, tests: {total}, parametrized: {param}")
