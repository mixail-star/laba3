import subprocess, html, sys
from pathlib import Path

OUT = Path(sys.argv[1])

def cls(name, attrs, methods, stereo=None, abstract=False, color="#ffffff"):
    e = html.escape
    title = (f'<tr><td><font point-size="10">«{e(stereo)}»</font></td></tr>' if stereo else '')
    nm = f'<i>{e(name)}</i>' if abstract else e(name)
    rows = [f'<tr><td bgcolor="#dbe8f7"><b>{nm}</b></td></tr>']
    def block(items):
        if not items:
            return '<tr><td> </td></tr>'
        cells = []
        for it in items:
            txt = e(it.lstrip('~'))
            cells.append(f'<i>{txt}</i>' if it.startswith('~') else txt)
        return '<tr><td align="left" balign="left">' + '<br align="left"/>'.join(cells) + '<br align="left"/></td></tr>'
    body = title + rows[0] + block(attrs) + block(methods)
    return f'"{name}" [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="4" bgcolor="{color}">{body}</table>>];'

def render(name, nodes, edges, rankdir="BT"):
    dot = ['digraph G {', f'rankdir={rankdir}; nodesep=0.35; ranksep=0.55;',
           'node [shape=plain, fontname="DejaVu Sans", fontsize=10]; edge [fontname="DejaVu Sans", fontsize=9];']
    dot += nodes + edges + ['}']
    src = '\n'.join(dot)
    (OUT / f'{name}.dot').write_text(src)
    subprocess.run(['dot', '-Tpng', '-Gdpi=170', '-o', str(OUT / f'{name}.png')], input=src.encode(), check=True)

INH = '[arrowhead=empty, arrowsize=1.1]'
REAL = '[arrowhead=empty, style=dashed, arrowsize=1.1]'
COMP = '[arrowtail=diamond, dir=back, arrowsize=1.1, label="  1"]'
DEP = '[style=dashed, arrowhead=vee, label=" «use»"]'

# 1. Общая иерархия (C++)
nodes = [
    cls('Serializable', [], ['~+save_binary(out: ostream&) : void', '~+load_binary(in: istream&) : void',
        '~+save_text(out: ostream&) : void', '~+load_text(in: istream&) : void',
        '+save(out, format: Format) : void', '+load(in, format: Format) : void',
        '+save_file(path, format) : void', '+load_file(path, format) : void'], stereo='interface', abstract=True),
    cls('Container', [], ['~+length() : int', '+empty() : bool', '~+clear() : void', '~+type_name() : string'], abstract=True),
    cls('Sequence', [], ['~+values() : Array', '+save_binary(out) : void', '+load_binary(in) : void',
        '+save_text(out) : void', '+load_text(in) : void', '~#restore(value: string) : void'], abstract=True),
    cls('HashTable', [], ['~+put(key, value) : bool', '~+get(key) : optional<string>', '~+remove(key) : bool',
        '+contains(key) : bool', '~+for_each_pair(visit) : void', '~+capacity() : int', '+load_factor() : double',
        '+save_binary(out) : void', '+load_binary(in) : void', '+save_text(out) : void', '+load_text(in) : void'], abstract=True),
    cls('Array', ['-data : string*', '-size : int', '-capacity : int'], ['+push_back(value)', '+insert(index, value) : bool',
        '+get(index, value&) : bool', '+set(index, value) : bool', '+erase(index, removed&) : bool', '+at(index) : string',
        '-resize()']),
    cls('SinglyList', ['-head : Node*', '-tail : Node*', '-count : int'], ['+push_front(v) / push_back(v)',
        '+insert_after(key, v) / insert_before(key, v) : bool', '+pop_front(out&) / pop_back(out&) : bool',
        '+remove(key) : bool', '+contains(key) : bool', '+get(i, out&) / front(out&) : bool']),
    cls('DoublyList', ['-head : Node*', '-tail : Node*', '-count : int'], ['+push_front(v) / push_back(v)',
        '+insert_after / insert_before : bool', '+pop_front(out&) / pop_back(out&) : bool', '+remove(key) : bool',
        '+get(i, out&) : bool', '-find(key) : Node*', '-unlink(node)']),
    cls('Stack', ['-list : SinglyList'], ['+push(value)', '+pop(out&) : bool', '+top(out&) : bool']),
    cls('Queue', ['-list : SinglyList'], ['+push(value)', '+pop(out&) : bool', '+front(out&) : bool']),
    cls('RBTree', ['-nil : Node*', '-root : Node*', '-count : int'], ['+insert(key) / erase(key) : bool',
        '+contains(key) : bool', '+min_key(out&) / max_key(out&) : bool', '+next(key, out&) / prev(key, out&) : bool',
        '+keys() / preorder() / inorder() / postorder() / bfs() : Array', '+diagram() : string', '+is_valid() : bool',
        '+save_/load_binary, save_/load_text', '-insert_fix(z) / erase_fix(x)', '-left_rotate(x) / right_rotate(x)']),
    cls('ChainHashTable', ['-buckets_ : Entry**', '-bucket_count_ : int', '-count_ : int'],
        ['+put / get / remove', '+longest_chain() : int', '-index(key) : int', '-rehash(new_count)']),
    cls('OpenHashTable', ['-probing_ : Probing', '-keys_, values_ : string*', '-cells_ : Cell*', '-count_, deleted_ : int'],
        ['+put / get / remove', '+probes(key) : int', '+is_prime(n) : bool {static}', '-probe(hash, i) : int',
         '-find(key, probes&) : int', '-rebuild(new_size)']),
]
edges = ['Container -> Serializable ' + INH, 'Sequence -> Container ' + INH, 'HashTable -> Container ' + INH]
edges += [f'{c} -> Sequence {INH}' for c in ['Array', 'SinglyList', 'DoublyList', 'Stack', 'Queue', 'RBTree']]
edges += [f'{c} -> HashTable {INH}' for c in ['ChainHashTable', 'OpenHashTable']]
edges += ['Stack -> SinglyList ' + COMP.replace('dir=back', 'dir=back, constraint=false'),
          'Queue -> SinglyList ' + COMP.replace('dir=back', 'dir=back, constraint=false'),
          'RBTree -> Array ' + DEP.replace(']', ', constraint=false]')]
render('uml_cpp', nodes, edges, rankdir='RL')

# 2. Сериализация: формат и вспомогательные функции
nodes = [
    cls('Format', ['Binary', 'Text'], [], stereo='enumeration'),
    cls('codec', [], ['+write_u32 / read_u32', '+write_string / read_string', '+write_binary_header(out, type, count)',
        '+read_binary_header(in, type) : uint32', '+write_json(out, type, values)', '+read_json(in, type) : Array',
        '-JsonString / WriteItem / ParseJson (ЛР №1)'], stereo='namespace'),
    cls('Serializable', [], ['~+save_binary / load_binary', '~+save_text / load_text', '+save / load (out, Format)',
        '+save_file / load_file (path, Format)'], stereo='interface', abstract=True),
    cls('Sequence', [], ['+save_binary: заголовок + строки', '+save_text: {"Тип": [значения]}'], abstract=True),
    cls('HashTable', [], ['+save_binary: заголовок + пары', '+save_text: [k1, v1, k2, v2]'], abstract=True),
    cls('RBTree', [], ['+save_binary / save_text: метки 20(B) (preorder)', '-attach(key, red)',
        '-load_labels(labels): проверка свойств']),
]
edges = ['Sequence -> Serializable ' + INH, 'HashTable -> Serializable ' + INH, 'RBTree -> Sequence ' + INH,
         'Serializable -> Format ' + DEP, 'Sequence -> codec ' + DEP, 'HashTable -> codec ' + DEP, 'RBTree -> codec ' + DEP]
render('uml_serialization', nodes, edges)

# 3. Rust: трейты и структуры
nodes = [
    cls('Serializable', [], ['~save_binary(&self, out: &mut dyn Write)', '~load_binary(&mut self, input: &mut dyn Read)',
        '~save_text / load_text', 'save / load (format) {default}', 'save_file / load_file {default}'], stereo='trait', abstract=True),
    cls('Container', [], ['~length(&self) -> usize', 'is_empty(&self) -> bool {default}', '~clear(&mut self)',
        '~type_name(&self) -> &str'], stereo='trait', abstract=True),
    cls('Sequence', [], ['~values(&self) -> Vec<String>', '~restore(&mut self, value: &str)'], stereo='trait', abstract=True),
    cls('HashTable', [], ['~put / get / remove', '~for_each_pair', '~capacity', 'contains / load_factor / pairs {default}'],
        stereo='trait', abstract=True),
    cls('Array', ['-data: Box<[String]>', '-size: usize'], ['+push_back / insert / get / set / erase', '+length / as_slice']),
    cls('SinglyList', ['-nodes: Vec<Option<Node>>', '-free: Vec<usize>', '-head, tail: Option<usize>'],
        ['+push_front / push_back / pop_*', '+insert_after / insert_before / remove', '+get / contains / front / values']),
    cls('DoublyList', ['-nodes: Vec<Option<Node>>', '-free: Vec<usize>', '-head, tail: Option<usize>'],
        ['+push_* / pop_* / insert_*', '+remove / get / contains / values']),
    cls('Stack', ['-list: SinglyList'], ['+push / pop / top / values']),
    cls('Queue', ['-list: SinglyList'], ['+push / pop / front / values']),
    cls('RBTree', ['-nodes: Vec<Node>', '-root: usize (0 = NIL)'], ['+insert / erase / contains', '+keys / preorder / bfs / is_valid']),
    cls('ChainHashTable', ['-buckets: Vec<Option<Box<Entry>>>'], ['+longest_chain()']),
    cls('OpenHashTable', ['-probing: Probing', '-keys, values: Vec<String>', '-cells: Vec<Cell>'], ['+probes(key)']),
]
edges = ['Container -> Serializable ' + INH, 'Sequence -> Container ' + INH, 'HashTable -> Container ' + INH]
edges += [f'{c} -> Sequence {REAL}' for c in ['Array', 'SinglyList', 'DoublyList', 'Stack', 'Queue', 'RBTree']]
edges += [f'{c} -> HashTable {REAL}' for c in ['ChainHashTable', 'OpenHashTable']]
edges += ['Stack -> SinglyList ' + COMP.replace('dir=back', 'dir=back, constraint=false'),
          'Queue -> SinglyList ' + COMP.replace('dir=back', 'dir=back, constraint=false')]
render('uml_rust', nodes, edges, rankdir='RL')
print('ok')
