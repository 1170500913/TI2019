def readMap():
    global map
    string = ''
    pattern = re.compile('<\d+,\d+>')
    with open('./code/map.txt', mode='r', encoding='utf-8') as f:
        for line in f:
            string = string + line
    
    # print(string)

    entrys = pattern.findall(string)
    map.clear()
    for entry in entrys:
        # print(entry)
        array = re.split('[,<>]', entry)
        key = int(array[1])
        value = int(array[2])
        map[key] = value

def writeMap():
    global map
    string = ''
    for key, value in map.items():
        string += '<' + str(key) + ',' + str(value) + '>'
    with open('./code/map.txt', mode='w', encoding='utf-8') as f:
        f.write(string)