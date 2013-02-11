import sys

def get_identifier(string):
    if string[12]!="0":
        print "ERROR: ", string
        print string[12]
        return (None, None)
    else:
        if string[17:20] == "\x33\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x31\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x32\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x38\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x39\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x37\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[16:19] == "\x31\xfc\x03":
            return (string[12:17] + "000" + string[19:21], 21)
        elif string[16:19] == "\x31\xfc\x04":
            return (string[12:17] + "0000" + string[19], 20)
        elif re.match(r"^\d+$", string[17:22]):
            return (string[12:22], 22)
        else:
            print "ERROR: " + string
            print ord(string[18]), ord(string[19]), ord(string[20])
            print  ":".join("{0:x}".format(ord(c)) for c in string[16:20])
            return (None,None)

def get_payment_details(string, number):
    res = []
    step = 14
    print number
    for i in range(0, number):
        offset = i*step
        amount = string[offset:offset+5]
        if amount == "10850":
            print "error"
            print ":".join("{0:x}".format(ord(c)) for c in string[offset+6])
            print ":".join("{0:x}".format(ord(c)) for c in string[offset:offset+7])
        offset = offset + len(amount)
        while string[offset] != "\x01":
            amount = amount + string[offset]
            offset += 1
        if len(amount) > 7:
            print "amount error"
            print ":".join("{0:x}".format(ord(c)) for c in string[offset+6: offset+50])
        date = string[offset:offset+4]

        date = ":".join("{0:x}".format(ord(c)) for c in date)
        method = string[offset+4]
        res.append((amount, date, method))
    return res
f = open("BST/llal")
lines = f.readlines()
content = "".join(lines)

class Student:
    def __init__(self, identifier, name, street, number, zip_code, city):
        self.identifier = identifier
        self.name = name
        self.street = street
        self.number = number
        self.zip_code = zip_code
        self.city = city
        self.payments = []

    def append_payments(self, payments):
        self.payments.append(payments)

    def to_string(self):
        res = self.identifier + " " + self.name
        res += "\n" + self.street + " " + self.number + "\n"
        res += self.zip_code + " " + self.city
        res += "\n" + str(self.payments)
        return res

import re
students = []

indexes = [m.end() for m in re.finditer('[\x00]{65}\x01', content)]

previous = 0
length = 450
for entry in indexes:
    previous += 1
    string = content[entry:entry+length]
    #regex = re.compile(r"([A-Z]{4})")
    #m = regex.match(string)
    (identifier, index) = get_identifier(string)
    if not identifier:
        continue
    print "----------------------------"
    print identifier
    temp = string[index: index + 25].split(chr(253))
    index = index + len(temp[0])
    name = temp[0]
    if string[index] == "\xfd":
        index = index + 2
    regex = re.compile(".*(\d{8})[ABCDE].*")
    m = regex.match(string[index:index+20])
    if string[index:index+5] == "\x32\x30\xfe\x31\x05":
        print "11111111"
        index = index + 6
    elif string[index:index+5] == "\x32\x30\xfe\x31\x04":
        print "11111111"
        index = index + 7
    elif m:
        print m.group(1)
        index = index + m.start() + 8
    else:
        print ":".join("{0:x}".format(ord(c)) for c in string[index: index+20])
        print "error: ", string[index: index + 20]

    ll_type = string[index: index+2]
    index = index + 2
    street = string[index: index+40].split(chr(253))[0]
    if len(street)>20:
        street = street[:20]
    index = index + len(street)
    if string[index] == "\xfd":
        index = index + 2

    m = re.match(r"(.*)(\d\d\d\d[A-Z][A-Z][A-Z\-]+\W)", string[index: index+40])
    if m:
        pattern = re.compile("[\W_]+")
        number = pattern.sub('',m.group(1))
        code = m.group(2)[:4]
        town = m.group(2)[4:-1]
        index = index + len(m.group(1) + m.group(2)) +1
    else:
        m = re.match(r"(.*)(\d..[A-Z][A-Z][A-Z]+\W)", string[index: index+40])
        if m:
            pattern = re.compile("[\W_]+")
            number = pattern.sub('',m.group(1))
            code = m.group(2)[0] + "000"
            town = m.group(2)[3:-1]
            index = index + len(m.group(1) + m.group(2)) +1
        else:
            print "error"
            print string[index: index+20]
            print ":".join("{0:x}".format(ord(c)) for c in string[index: index+20])
            sys.exit()

    students.append(Student(identifier, name, street, number, code, town))
    #if string[index] == "\xfd":
        #index = index + 2
    #m = re.match(r"([A-Z\-]+\W)", string[index: index+30])
    #if m:
        #place_of_birth = m.group(1)[:-1]
        #index = index + len(place_of_birth)
    #else:
        #print "error"
        #print string[index: index+20]
        #print ":".join("{0:x}".format(ord(c)) for c in string[index: index+20])
    #print place_of_birth
    #m = re.match(r".*\D([\d]{6}\d+\D)", string[index: index+30])
    #if m:
        #print m.group(1)[:12]
#
    #else:
        #print "error"
        #print string[index: index+20]
        #print ":".join("{0:x}".format(ord(c)) for c in string[index: index+20])


f = open("BST/llbe")

lines = f.readlines()

content = "".join(lines)

indexes = [m.start() for m in re.finditer('012....?..\d', content)]

payment_details = {}
for i in indexes:
        if content[i+5:i+7] == "\xfc\x03":
            identifier = content[i:i+5] + "000" + content[i+7:i+9]
        elif content[i+6:i+8] == "\xfc\x03":
            identifier = content[i:i+6] + "000" + content[i+8:i+9]
        else:
            identifier = content[i:i+10]
            currency = content[i+10]
        try:
            int(identifier)
        except ValueError:
            print "invalid identifier error", identifier
            print ":".join("{0:x}".format(ord(c)) for c in identifier)
            continue
        m = re.match(r".*\W(\d\d)", content[i+11:i+100])
        try:
            nb_payments = int( content[i+23:i+25])
            print identifier 
            payments = get_payment_details(content[i+27:], nb_payments)
            if not payment_details.has_key(identifier):
                payment_details[identifier] = []
            payment_details[identifier].append(payments)
        except ValueError:
            print "nb of payments error", identifier
            pass
for entry in students:
    try:
        entry.append_payments(payment_details[entry.identifier])
    except KeyError:
        #print "no payments for: " + entry.identifier
        pass
    print "-----------------------------"
    print entry.to_string()

sys.exit()
