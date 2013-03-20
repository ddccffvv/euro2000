from flask import Flask, url_for, request, Response
from flask import render_template
import sys, struct, re, json, sqlite3
from datetime import date
from functools import wraps
from secrets import user, passwd, debug

def check_auth(username, password):
    return username == user and password == passwd

def authenticate():
    return Response(
            "Could not verify access level for url.\n"
            "You have to login with proper credentials", 401,
            {'WWW-Authenticate': 'Basic realm="Login Required'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def expand_string(string):
    res = string
    while "\xfc" in res:
        number = res[res.find("\xfc")+1]
        if number == "\x03":
            res = res.replace("\xfc\x03", "\x30\x30\x30")
        elif number == "\x04":
            res = res.replace("\xfc\x04", "\x30\x30\x30\x30")
        elif number == "\x05":
            res = res.replace("\xfc\x05", "\x30\x30\x30\x30\x30")
        elif number == "\x06":
            res = res.replace("\xfc\x06", "\x30\x30\x30\x30\x30\x30")
        else:
            break
    return res


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
    temp = string.split("\xfd\x08\xfc\x08")[0]
    entries = temp.split("\xfd\x08")

    for e in entries:
        etemp = expand_string(e)
        payment_method = etemp[12]
        if payment_method not in ["B","C","K"]:
            payment_method = "U"
        try:
            d = str(struct.unpack(">I", etemp[8:12])[0])
            pay_date = date(int(d[:4]),int(d[4:6]),int(d[6:]))
            res.append((int(etemp[:8]),pay_date, payment_method))
        except ValueError:
            print "oops in append!!"
            print etemp[:8]
    return res


class Student:
    def __init__(self, identifier, name, street, number, zip_code, city):
        self.identifier = identifier
        self.name = unicode(name, "cp1252")
        self.street = unicode(street, "cp1252")
        self.number = number
        self.zip_code = zip_code
        self.city = city
        self.payments = []
        self.unique = "1" + "/" + self.identifier[6:] + "/" + self.identifier[2:6]

    def append_payments(self, payments):
        self.payments.extend(payments)

    def get_payments_between(self, date1, date2):
        return filter(lambda (x,y,z): date1 <= y <= date2, self.payments)

    def get_header(self):
        res = self.identifier + " " + self.name
        res += "\n" + self.street + " " + self.number + "\n"
        res += self.zip_code + " " + self.city
        return res

    def to_string(self):
        res = self.identifier + " " + self.name
        res += "\n" + self.street + " " + self.number + "\n"
        res += self.zip_code + " " + self.city
        res += "\n" + str(self.payments)
        return res

def read_database_files():
    f = open("BST/llal")
    lines = f.readlines()
    content = "".join(lines)
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
        temp = string[index: index + 25].split(chr(253))
        index = index + len(temp[0])
        name = temp[0]
        if string[index] == "\xfd":
            index = index + 2
        regex = re.compile(".*(\d{8})[ABCDE].*")
        m = regex.match(string[index:index+20])
        if string[index:index+5] == "\x32\x30\xfe\x31\x05":
            print identifier
            print "11111111"
            index = index + 6
        elif string[index:index+5] == "\x32\x30\xfe\x31\x04":
            print identifier
            print "11111111"
            index = index + 7
        elif m:
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

    f = open("BST/llbe")

    lines = f.readlines()

    content = "".join(lines)

    indexes = [m.start() for m in re.finditer('012....?..\dE', content)]

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
                if content[i+5:i+7] == "\xfc\x03":
                    if content[i+22:i+24] == "\x31\xfc":
                        nb_payments = 10
                        payments = get_payment_details(content[i+24:], nb_payments)
                    elif content[i+22:i+24] == "\xfc\x0a" or content[i+22:i+24] == "\xfd\x08" or content[i+22:i+24] == "\x08\xfc":
                        nb_payments = 0
                        payments = []
                    else:
                        #print ":".join("{0:x}".format(ord(c)) for c in content[i+22:i+24])
                        nb_payments = int( content[i+22:i+24])
                        payments = get_payment_details(content[i+24:], nb_payments)
                elif content[i+6:i+8] == "\xfc\x03":
                    if content[i+22:i+24] == "\x31\xfc":
                        nb_payments = 10
                        payments = get_payment_details(content[i+24:], nb_payments)
                    elif content[i+22:i+24] == "\xfc\x0a" or content[i+22:i+24] == "\xfd\x08" or content[i+22:i+24] == "\x08\xfc":
                        nb_payments = 0
                        payments = []
                    else:
                        #print ":".join("{0:x}".format(ord(c)) for c in content[i+22:i+24])
                        nb_payments = int( content[i+22:i+24])
                        payments = get_payment_details(content[i+24:], nb_payments)
                else:
                    if content[i+23:i+25] == "\x31\xfc":
                        nb_payments = 10
                        payments = get_payment_details(content[i+24:], nb_payments)
                    elif content[i+23:i+25] == "\xfc\x0a" or content[i+23:i+25] == "\xfd\x08" or content[i+23:i+25] == "\x08\xfc":
                        nb_payments = 0
                        payments = []
                    else:
                        #print ":".join("{0:x}".format(ord(c)) for c in content[i+23:i+25])
                        nb_payments = int( content[i+23:i+25])
                        payments = get_payment_details(content[i+25:], nb_payments)
                if not payment_details.has_key(identifier):
                    payment_details[identifier] = []
                payment_details[identifier].extend(payments)
            except ValueError:
                if int(identifier[2:6]) > 2011:
                    print "nb of payments error", identifier
                    print ":".join("{0:x}".format(ord(c)) for c in content[i: i+10])
                    print ":".join("{0:x}".format(ord(c)) for c in content[i+22:i+26])
                    print ":".join("{0:x}".format(ord(c)) for c in content[i+12:i+65])
                    print content[i+12:i+65]
                pass
    for entry in students:
        #print "-----------------------------"
        try:
            entry.append_payments(payment_details[entry.identifier])
        except KeyError:
            #print "no payments for: " + entry.identifier
            pass
        #print entry.to_string()
    students.reverse()
    return students

def get_students_with_payments_between(students, date1, date2):
    return filter(lambda s: s.get_payments_between(date1, date2), students)


students = read_database_files()

feb = get_students_with_payments_between(students, date(2013,2,1), date(2013,2,28))


app = Flask(__name__)

@app.route('/')
@requires_auth
def home():
    return render_template('index.html')

@app.route('/hello')
@requires_auth
def hello():
    return render_template('test.html')

@app.route('/save-invoice', methods=["POST"])
@requires_auth
def save_invoice():
    data = json.loads(request.form["data"])
    conn = sqlite3.connect("database")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO invoices(reference, date, nummer, total) VALUES(?,?,?,?)",(data["referentie"], data["date"], data["nummer"], data["due"]))
    conn.commit()
    invoice_id = cursor.lastrowid
    for entry in data["entries"]:
        print entry["code"]
        cursor.execute("INSERT INTO invoice_entries(factuur_id, code, omschrijving, cost, btw, qty) VALUES(?,?,?,?,?,?)",(invoice_id, entry["code"], entry["omschrijving"], entry["cost"], entry["btw"], entry["qty"]))
    conn.commit()
    conn.close()
    return request.form["data"]

@app.route('/list_students')
@requires_auth
def list_students():
    s = []

    for entry in students:
        #payments = entry.get_payments_between(begin, end)
        s.append(entry)

    return render_template('student_list.html', students = s)

@app.route('/list_feb')
@requires_auth
def list_feb():
    s = []

    for entry in feb:
        #payments = entry.get_payments_between(begin, end)
        s.append(entry)

    return render_template('febstudent_list.html', students = s)

@app.route('/student/<int:identifier>')
@requires_auth
def student(identifier):
    identifier = identifier - 1
    if identifier < len(students):
        if (identifier -1) < 0:
            ppu = url_for('list_students')
        else:
            ppu = url_for('student',identifier = identifier)
        if (identifier + 1) > len(students):
            npu = url_for('list_students')
        else:
            bla = identifier + 2
            npu = url_for('student', identifier = bla)
        return render_template('student.html', identifier = identifier+1,student = students[identifier], next_profile_url = npu, previous_profile_url = ppu)
    else:
        return list_students()
@app.route('/reload_data')
@requires_auth
def reload_data():
    global students
    students = read_database_files()
    return "done"

@app.route('/invoice/<int:identifier>')
@requires_auth
def invoice(identifier):
    conn = sqlite3.connect("database")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices where reference=?", (students[identifier-1].unique, ))
    rows = cursor.fetchall()
    rows = list(rows)
    if len(rows)<1:
        rows = None
    return render_template('invoice.html', student = students[identifier-1], invoices = rows)

@app.route('/feb/<int:identifier>')
@requires_auth
def february(identifier):
    return render_template('febinvoice.html', student = feb[identifier-1])

if __name__ == '__main__':
    if debug:
        app.debug = True
        app.run()
    else:
        app.run(host="0.0.0.0", port=4343)
