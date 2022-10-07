from flask import Flask,render_template,request,redirect,flash
import pyrebase
firebaseConfig = {
  "apiKey": "AIzaSyD0KS2N_37H5Pikp3pkAS5BhLkzVqMMIfE",
  "authDomain": "fir-demo-9f71c.firebaseapp.com",
  "databaseURL": "https://fir-demo-9f71c-default-rtdb.firebaseio.com",
  "projectId": "fir-demo-9f71c",
  "storageBucket": "fir-demo-9f71c.appspot.com",
  "messagingSenderId": "586782017358",
  "appId": "1:586782017358:web:2c324717d215942025001f",
  "measurementId": "G-DRSD92QYY1"
}
firebase=pyrebase.initialize_app(firebaseConfig)
db=firebase.database()

app = Flask(__name__)

#global variables

user_owner=False
user_cash=False
user_store=False


@app.route("/",methods=['GET','POST'])
def maain():
    global user_owner
    global user_cash
    global user_store
    user_store=False
    user_owner=False
    user_cash=False

    if request.method == 'POST':
        email=request.form['email']
        password=request.form['password']
        print('email '+email+' password '+password)
        if email== 'owner@shs.com' and password =='Complicated#123':
            print('i am here')
            user_owner=True
            return redirect("/welcome/")
        if email=='store@shs.com' and password=='store#123':
            user_store=True
            return redirect("/welcome/")
        if email=='cash@shs.com' and password=='cash#123':
            user_cash=True
            return redirect("/welcome/")
        else:
            print('invalid credentials')
    #default return value as index.html
    return render_template("index.html")

@app.route("/welcome/")
def home():
    if user_cash:
        print('i am cash')
    if user_owner:
        print('i am owner')
    if user_store:
        print('i am store')
        return  redirect("/store/")
    return render_template("welcome.html")

def getItems():
    itemObj=db.child("inventory").get()
    itemDics=itemObj.val()
    del itemDics['issue']
    return itemDics

@app.route("/store/")
def store():
    #getting state of inventory
    items=getItems()
    print(items)

    return render_template("store.html",items=items)

def getAllSuppliers():
    supObj=db.child('supplier').get().val()
    lst=list(supObj.keys())
    lst.remove('totalPurchase')
    lst=set(lst)
    return lst


@app.route("/store/recieve" ,methods=['GET','POST'])
def recieving():
    allSupliers=getAllSuppliers()
    if request.method == 'POST':
        supName=request.form['supName']
        if supName in allSupliers:
            print('i am in supplier'+supName)
            urlstr='/store/recieve/'+str(supName)
            return redirect(urlstr)

    return render_template("recieve.html",allSupliers=allSupliers)

def getDetailsOfAllSuppliers():
    ans={}

    allNames=getAllSuppliers()
    supObj=db.child('supplier').get().val()
    for sup in supObj:
        if sup in allNames:
            supplier=supObj[sup]
            del supplier['orders']
            ans[sup]=supplier
    return ans

@app.route("/store/suppliers")
def showSuppliers():
    allSuppliersDetails=getDetailsOfAllSuppliers()

    return render_template("suppliers.html",allSuppliersDetails=allSuppliersDetails)

current_order_dict={'total':0}
def addToDict(itemName,quantity):

    current_order_dict[itemName]=quantity

@app.route("/store/recieve/<supName>" , methods=['GET','POST'])
def recieve(supName):
    print(supName+" recieved ")
    supplierDetails=getDetailsOfAllSuppliers()[supName]

    if request.method == 'POST':
        itemName=request.form['EnteredItemName']
        quanity=request.form['EnteredQuantity']
        addToDict(itemName,quanity)
        print(current_order_dict)
    return render_template("orderRecieving.html",supName=supName,supplierDetails=supplierDetails,current_order_dict=current_order_dict)

def updateCurrentStateOfInventory(ordersDict):
    #priceList  =[3000,'kg',30] [total price, unit, quanity]
    #ordersDict['total'] doesnt have the pricelist
    for itemName,priceList in ordersDict.items():
        if itemName!='total':
            itemDBObject=db.child('inventory').child(itemName).get().val() #[30,'kg']
            if itemDBObject != None:
                itemDBObject[0]=itemDBObject[0]+priceList[2] #adding current quanytiy and order quanity
            else:
                itemDBObject=[]
                itemDBObject.append(priceList[1])
                itemDBObject.append(priceList[2])
            db.child('inventory').update({itemName:itemDBObject}) #updating the item


def getMinimumSupplier(item):
    min_data = [99999]
    min_sup = 'no supplier'
    allSuppliers = getDetailsOfAllSuppliers()
    for supplier, items in allSuppliers.items():

        if item in items:
            price = items[item][0]
            if price < min_data[0]:
                min_data[0] = price
                min_sup = supplier
    min_data.append(min_sup)
    return min_data

def updateTotalWorthInventory():
    total=0
    current_state=db.child('inventory').get().val()
    for item in current_state:
        if item =='totalWorth' or item == 'issue':
            continue
        quantity=current_state[item][0]
        minPrice=getMinimumSupplier(item)[0]
        total+=quantity*minPrice
    print(total)
    db.child('inventory').update({'totalWorth':total})


@app.route("/store/placeOrder/<supName>")
def placingOrder(supName):
    print("placing orders for "+supName)
    print(current_order_dict)
    prices_sup=db.child("supplier").child(supName).get().val()
    #print(prices_sup)
    for recieved_item in current_order_dict:
        if recieved_item in prices_sup:
            item_price=prices_sup[recieved_item]
            quantity=current_order_dict[recieved_item]
            item_price[0]=int(item_price[0])*int(quantity)
            current_order_dict['total']+=item_price[0]
            item_price.append(int(quantity))
            current_order_dict[recieved_item]=item_price
        else:
            print(recieved_item+" is not there on the db for this supplier "+supName)

    print('final order list on db \n')
    print(current_order_dict)

    # placing order for supName with current_order_dict

    db.child("supplier").child(supName).child("orders").push(current_order_dict)

    #updating state of inventory

    updateCurrentStateOfInventory(current_order_dict)
    updateTotalWorthInventory()

    current_order_dict.clear() #removing the items in dictionary
    current_order_dict['total']=0


    return redirect("/store/")


app.run(debug=True)