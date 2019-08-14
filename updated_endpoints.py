import flask
from flask import jsonify # <- `jsonify` instead of `json`
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import request, render_template, url_for, redirect, send_from_directory, flash
from flask import Response

from routetest1_InsertValuesIntoDB_customer import Customer
from routetest1_InsertValuesIntoDB_models import Models
from routetest1_InsertValuesIntoDB_execution import Execution
from routetest1_InsertValuesIntoDB_datasets import Datasets
from werkzeug.utils import secure_filename
from sqlalchemy import update, func
from sqlalchemy.ext.declarative import DeclarativeMeta
import flask
import decimal, datetime
import json
import pprint
import sys
import importlib
import os
import errno
from sqlalchemy.inspection import inspect
import zipfile


UPLOAD_FOLDER = "/home/chiefai/production/data"
ALLOWED_EXTENSIONS = set(['txt', 'csv', 'pdf', 'png', 'jpg', 'jpeg', 'tif', 'tiff', 'gif', 'h5', 'pkl', 'py', 'joblib', 'zip'])

# Initialise the Flask app
app = flask.Flask(__name__, template_folder='templates')
#app = Flask("__name_")


def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers
    return response
app.after_request(add_cors_headers)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        """JSON encoder function for SQLAlchemy special classes."""
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class AlchemyEncoder(json.JSONEncoder):
 def default(self, obj):
     if isinstance(obj.__class__, DeclarativeMeta):
     # an SQLAlchemy class
        fields = {}
        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
            data = obj.__getattribute__(field)
            try:
                json.dumps(data) # this will fail on non-encodable values, like other classes
                fields[field] = data
            except TypeError:
                fields[field] = None
       # a json-encodable dict
        return fields
     return json.JSONEncoder.default(self, obj)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def uploaded_file_UpdateDatasetsTable(filename):
    if flask.request.method == 'GET':
        datasetID = Datasets.query.filter_by(datasets_id=datasets_id).first()
        customerID = Customer.query.filter_by(customer_id=customer_id).first().customer_id
        datasetfilepath = Datasets.query.filter_by(datasets_id=datasets_id).first().datasetsfilepath
        datasets_table = Datasets(datasetsID, customerID, datasetfilepath , 'NOW()')
        db.session.add(datasets_table)
        db.session.commit()
        return(filename, "DATA added successfully using GET METHOD")

    if flask.request.method == 'POST':
        datasetID = flask.request.form['datasets_id']
        customerID = flask.request.form['customer_id']
        datasetfilepath = flask.request.form['datasetsfilepath']
        datasets_table = Datasets(datasets_id=datasetsID, customer_id=customerID, datasetsfilepath=datasetfilepath , created_on='NOW()')
        db.session.add(datasets_table)
        db.session.commit()
        return (filename, "DATA added successfully using POST METHOD")


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://chiefai:123456@localhost:5433/chiefai1'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
engine = create_engine("postgresql://chiefai:123456@localhost:5433/chiefai1")
Session = sessionmaker(bind=engine)
session=Session()
db = SQLAlchemy(app)
app.json_encoder = DecimalEncoder


class Serializer(object):

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


class Customer(db.Model, Serializer):
    customer_id = db.Column(db.Integer, primary_key=True)
    customername = db.Column(db.String(100))
    credits = db.Column(db.Integer)
    created_on = db.Column(db.DateTime, default=db.func.now())

    def __init__(self, customer_id, customername, credits, created_on):
        self.customer_id = customer_id
        self.customername = customername
        self.credits = credits
        self.created_on = created_on

    def serialize(self):
        d = Serializer.serialize(self)
        return d


class Models(db.Model, Serializer):
    model_id = db.Column(db.Integer, primary_key=True)
    modelname = db.Column(db.String(100))
    modelscriptpath = db.Column(db.String(100))
    modelpath = db.Column(db.String(100))
    supplier_id = db.Column(db.Integer)
    created_on = db.Column(db.DateTime, default=db.func.now())
    last_login = db.Column(db.DateTime, default=db.func.now())
    price = db.Column(db.Integer)

    def __init__(self, model_id, modelname, modelscriptpath, modelpath, supplier_id, created_on, last_login, price):
        self.model_id = model_id
        self.modelname = modelname
        self.modelscriptpath = modelscriptpath
        self.modelpath = modelpath
        self.supplier_id = supplier_id
        self.created_on = created_on
        self.last_login = last_login
        self.price = price

    def serialize(self):
        d = Serializer.serialize(self)
        return d


class Execution(db.Model, Serializer):
    execution_id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer)
    customer_id = db.Column(db.Integer)
    created_on = db.Column(db.DateTime, default=db.func.now())
    result = db.Column(db.Numeric)
    charged_credits = db.Column(db.Numeric)
    commission_earned_chiefai = db.Column(db.Numeric)

    def __init__(self, execution_id, model_id, customer_id, created_on, result, charged_credits, commission_earned_chiefai):
        self.execution_id = execution_id
        self.model_id = model_id
        self.customer_id = customer_id
        self.created_on = created_on
        self.result = result
        self.charged_credits = charged_credits
        self.commission_earned_chiefai = commission_earned_chiefai

    def serialize(self):
        d = Serializer.serialize(self)
        return d


class Datasets(db.Model, Serializer):
    datasets_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer)
    datasetsfilepath = db.Column(db.String(100))
    created_on = db.Column(db.DateTime, default=db.func.now())

    def __init__(self, datasets_id, customer_id, datasetsfilepath, created_on):
        self.datasets_id = datasets_id
        self.customer_id = customer_id
        self.datasetsfilepath = datasetsfilepath
        self.created_on = created_on

    def serialize(self):
        d = Serializer.serialize(self)
        return d


class Supplier(db.Model, Serializer):
    supplier_id = db.Column(db.Integer, primary_key=True)
    suppliername = db.Column(db.String(100))
    commission = db.Column(db.Integer)
    created_on = db.Column(db.DateTime, default=db.func.now())

    def __init__(self, supplier_id, suppliername, commission, created_on):
        self.supplier_id = supplier_id
        self.suppliername = suppliername
        self.commission = commission
        self.created_on = created_on

    def serialize(self):
        d = Serializer.serialize(self)
        return d

# ###############################   MODELS   ########################################
# ###############################            ########################################

# 1 - INSERT/CREATE NEW USER

@app.route('/insert_model', methods=['POST'])
def insertModel():
    newModel_id = request.form['model_id']
    newModelname = request.form['model_name']
    newModelscriptpath = request.form['model_scriptpath']
    newModelpath = request.form['model_path']
    newSupplier_id = request.form['supplier_id']
    newCreated_on = request.form['created_on']
    newLast_login = request.form['last_login']
    newPrice = request.form['price']
    Model = Models(newModel_id, newModelname, newModelscriptpath, newModelpath, newSupplier_id, newCreated_on, newLast_login, newPrice)
    db.session.add(Model)
    db.session.commit()
    return "<p>Data is updated</p>"


# 2 - LIST RECORD

@app.route('/find_model/<modelname>')
def findModel(modelname):
    from appv1_Working import main
    models = Models.query.filter_by(modelname=modelname).first()
    return render_template('detail_models.html', myModels=models)


# 3 - LIST ALL RECORDS

@app.route('/list_all_models')
def listAllModels():
    models = Models.query.all()
    #models = Models.query.filter_by(model_id=9).first().model_id
    #model = int(models)
    #return str(models)
    return render_template('list_all_models.html', myModels=models)


@app.route('/execute/AllModelsJsonify.json', methods=['GET', 'POST'])
def DisplayAllModelsInJsonifyMode():
    allModels = Models.query.all()
    return jsonify(allModels=Models.serialize_list(allModels))


# 4 - EDIT RECORD



# 5 - RETRIEVE RECORD

@app.route('/execute/<modelname>/ModelsJsonify', methods=['GET', 'POST'])
def DisplayModelsInJsonifyMode(modelname):
    allModels = Models.query.filter_by(modelname=modelname).first()
    return jsonify(Model_ID=allModels.model_id, ModelName=allModels.modelname,
                   ModelScriptPath=allModels.modelscriptpath, ModelPath=allModels.modelpath,
                   SupplierID=allModels.supplier_id, Created_On=allModels.created_on,
                   Last_Login=allModels.last_login, Price=allModels.price)


# 6 - DELETE RECORD



# 7 - UPLOAD MODEL

####
@app.route('/uploadModelAndExecutor/<supplier_id>', methods=['GET', 'POST'])
def upload_BothModelAndExecutorAndUpdateModelsTable(supplier_id):
    if request.method == 'POST':
        fileA = request.files['fileA']
        filenameA = secure_filename(fileA.filename)
        if fileA and allowed_file(filenameA):
            executor_dir = "/home/chiefai/production/suppliers/supplier_" + str(supplier_id) + "/executor" # check if model folder exist$
            executorPath = os.path.join(executor_dir, filenameA)
            if os.path.exists(executorPath):
               raise Exception('An error occurred Executor Path exists')
            else:
               os.makedirs(executor_dir, exist_ok=True) # In this line os.makedirs("path/to/directory", exist_ok=True) makes it accept multiple files in the same directory or foler (i.e in our case /production/customer_"Whatever customerID"/models/".h5 or .pkl models")
               fileA.save(executorPath)
        else: raise Exception('An error occurred Executor Dir exists')

    if request.method == 'POST':
        fileB = request.files['fileB']
        filenameB = secure_filename(fileB.filename)
        if fileB and allowed_file(filenameB):
            model_dir = "/home/chiefai/production/suppliers/supplier_" + str(supplier_id) + "/models" # check if model folder exist$
            modelPath = os.path.join(model_dir, filenameB)
            if os.path.exists(modelPath):
               raise Exception('An error occurred Model Path exists')
            else:
               os.makedirs(model_dir, exist_ok=True) # In this line os.makedirs("path/to/directory", exist_ok=True) makes it accept$
               fileB.save(modelPath)
        else: raise Exception('An error occurred Model Dir exists')

        var1 = request.form['model_id']
        var2 = request.form['modelname']
        ## modelpath has been sperately defined ##
        #var4 = request.form['supplier_id']
        var5 = supplier_id
        var6 = request.form['created_on']
        var7 = request.form['last_login']
        var8 = request.form['commission_rate_model']
        models_table = Models(var1, var2, executorPath, modelPath, var5, var6, var7, var8)
        db.session.add(models_table)
        db.session.commit()
        return redirect(url_for('uploaded_modelAndExecutor', filenameA=filenameA, filenameB=filenameB))
        #return ("done")
    return '''
    <!doctype html>
    <title>Upload a new Model File Path</title>
    <h2>Please Upload your File (please be reminded only files with the following file extesions can be accepted ['txt', 'csv', 'pdf', 'png', 'jpg', 'jpeg', 'tif', 'tiff', 'gif', 'h5', 'pkl', 'py'])</h2>
    <form action="" method=post enctype=multipart/form-data>
    <p>ModelID: <input type=text name=model_id></p>
    <p>ModelName: <input type=text name=modelname></p>
    <p>SupplierID: <input type=text name=supplier_id></p>
    <p>Created_On: <input type=date name=created_on></p>
    <p>Last_Login: <input type=date name=last_login></p>
    <p>Commission_Rate_Model: <input type=number name=commission_rate_model></p>
      <p>Upload Model Executor Script [should be a '.py'(Python file)]: <input type=file name=fileA></p>
      <p>Upoad a Model (.h5 or .pkl file): <input type=file name=fileB></p>
         <input type=submit value=Upload></p>
         <input type="button" value="Go back!" onclick="history.back()">
    </form>
    '''

@app.route('/showUploadedModel/<filenameA>/<filenameB>', methods=['GET', 'POST'])
def uploaded_modelAndExecutor(filenameA, filenameB):
    return render_template('UploadModelAndExecutor.html', filenameA=filenameA, filenameB=filenameB)

@app.route('/OncefileisIsUploaded/<filenameA>/<filenameB>')
def send_modelandexecutor_UpdateModelsTable(filenameA, filenameB):
        return send_from_directory(UPLOAD_FOLDER, filename)

#####



# ###############################   CUSTOMERS   #####################################
# ###############################               #####################################

# 1 - INSERT/CREATE NEW RECORD
@app.route('/AddRecordCustomer', methods=['GET', 'POST'])
def AddRecordCustomer():
 if request.method == 'POST':
    newcustomer_id = request.form['customer_id']
    newcustomername = request.form['customername']
    newcredits = request.form['credits']
    newcreated_on = request.form['created_on']
    customer = Customer(newcustomer_id, newcustomername, newcredits, newcreated_on)
    db.session.add(customer)
    db.session.commit()
    print ("Record ADDED Successfully!")
    CustomerRecords = Customer.query.all()
    return jsonify(CustomerRecords = Customer.serialize_list(CustomerRecords))


# 2 - LIST RECORD
@app.route('/execute/<customer_id>/CustomersJsonify', methods=['GET', 'POST'])
def DisplayCustomersInJsonifyMode(customer_id):
    allCustomer = Customer.query.filter_by(customer_id=customer_id).first()
    return jsonify(Customer_ID=allCustomer.customer_id, CustomerName=allCustomer.customername,
                   Credits=allCustomer.credits, Created_On=allCustomer.created_on)


## 2.5 - QUERY RECORD BY SUPPLIER ID FROM WEB FORM/POSTMAN
@app.route('/execute/DisplayQueryModelsJsonify.json', methods=['GET', 'POST'])
def DisplayQueryModelsInJsonifyMode():
 if request.method == 'POST':
    var1 = request.form['supplier_id']
    allModels = Models.query.filter_by(supplier_id=var1).all()
    return jsonify(allModels = Models.serialize_list(allModels))


# 3 - LIST ALL RECORDS
@app.route('/execute/AllCustomersJsonify.json', methods=['GET', 'POST'])
def DisplayAllCustomersInJsonifyMode():
    allCustomer = Customer.query.all()
    return jsonify(allCustomer = Customer.serialize_list(allCustomer))


# 4 - EDIT RECORD



# 5 - DELETE RECORD
@app.route('/DeleteRecordCustomer', methods=['GET', 'POST'])
def DeleteRecordCustomer():
 if request.method == 'POST':
    var1 = request.form['customer_id']
    customerID = var1
    DeleteRecord = Customer.query.filter_by(customer_id=var1).first()
    db.session.delete(DeleteRecord)
    db.session.commit()
    print ("Record DELETED Successfully!")
    CustomerRecords = Customer.query.all()
    return jsonify(CustomerRecords = Customer.serialize_list(CustomerRecords))


# ###############################   CUSTOMER CREDITS   ####################################
# ###############################                      ####################################

@app.route('/TopUpCreditsCustomer', methods=['GET', 'POST'])
def AddCredits():
 if request.method == 'POST':
    var1 = request.form['credits']
    var2 = request.form['customer_id']
    customerID = var2
    A = Customer.query.filter_by(customer_id=var2).first().credits
    B = int(var1)
    AddCredits = A + B
    customerName = Customer.query.filter_by(customer_id=var2).first().customername
    updatedBalance = Customer(customerID, customerName, AddCredits, 'NOW()')
    db.session.merge(updatedBalance)
    db.session.commit()
    return str(AddCredits)

@app.route('/DeductCreditsCustomer', methods=['GET', 'POST'])
def DeductCredits():
 if request.method == 'POST':
    var1 = request.form['credits']
    var2 = request.form['customer_id']
    customerID = var2
    A = Customer.query.filter_by(customer_id=var2).first().credits
    B = int(var1)
    DeductCredits = A - B
    customerName = Customer.query.filter_by(customer_id=var2).first().customername
    updatedBalance = Customer(customerID, customerName, DeductCredits, 'NOW()')
    db.session.merge(updatedBalance)
    db.session.commit()
    return str(DeductCredits)

@app.route('/RetrieveCreditsCustomer', methods=['GET', 'POST'])
def RetrieveCredits():
 if request.method == 'POST':
    var1 = request.form['customer_id']
    customerID = var1
    RetrieveBalance = Customer.query.filter_by(customer_id=var1).first()
    #return str(RetrieveBalance)
    return jsonify(CustomerID=RetrieveBalance.customer_id, CustomerName=RetrieveBalance.customername,
                   Current_Balance_Credits=RetrieveBalance.credits, Created_On=RetrieveBalance.created_on)


# ###############################   SUPPLIERS   #####################################
# ###############################               #####################################

# 1 - INSERT/CREATE RECORD

@app.route('/AddRecordSupplier', methods=['GET', 'POST'])
def AddRecordSupplier():
 if request.method == 'POST':
    newsupplier_id = request.form['supplier_id']
    newsuppliername = request.form['suppliername']
    newcommission = request.form['commission']
    newcreated_on = request.form['created_on']
    supplier = Supplier(newsupplier_id, newsuppliername, newcommission,newcreated_on)
    db.session.add(supplier)
    db.session.commit()
    print ("Record ADDED Successfully!")
    SupplierRecords = Supplier.query.all()
    return jsonify(SupplierRecords = Supplier.serialize_list(SupplierRecords))


# 2 - EDIT RECORD

# 3 - DELETE RECORD

@app.route('/DeleteRecordSupplier', methods=['GET', 'POST'])
def DeleteRecordSupplier():
 if request.method == 'POST':
    var1 = request.form['supplier_id']
    supplierID = var1
    DeleteRecord = Supplier.query.filter_by(supplier_id=var1).first()
    db.session.delete(DeleteRecord)
    db.session.commit()
    print ("Record DELETED Successfully!")
    SupplierRecords = Supplier.query.all()
    return jsonify(SupplierRecords = Supplier.serialize_list(SupplierRecords))


# 4 - LIST RECORD

# 5 - LIST ALL RECORDS

# 6 - RETRIEVE RECORD

@app.route('/execute/AllSuppliersJsonify.json', methods=['GET', 'POST'])
def DisplayAllSuppliersInJasonifyMode():
    #dataset = Datasets.query.filter_by(datasets_id=datasets_id).first()
    allSuppliers = Supplier.query.all()
    return jsonify(allSuppliers = Supplier.serialize_list(allSuppliers))


# ###############################   SUPPLIER COMMISSION   ####################################
# ###############################                         ####################################

@app.route('/TopUpCommissionSupplier', methods=['GET', 'POST'])
def AddCommission():
 if request.method == 'POST':
    var1 = request.form['commission']
    var2 = request.form['supplier_id']
    supplierID = var2
    A = Supplier.query.filter_by(supplier_id=var2).first().commission
    B = int(var1)
    AddCommission = A + B
    supplierName = Supplier.query.filter_by(supplier_id=var2).first().suppliername
    updatedBalance = Supplier(supplierID, supplierName, AddCommission, 'NOW()')
    db.session.merge(updatedBalance)
    db.session.commit()
    return str(AddCommission)


@app.route('/DeductCommissionSupplier', methods=['GET', 'POST'])
def DeductCommission():
 if request.method == 'POST':
    var1 = request.form['commission']
    var2 = request.form['supplier_id']
    supplierID = var2
    A = Supplier.query.filter_by(supplier_id=var2).first().commission
    B = int(var1)
    DeductCommission = A - B
    supplierName = Supplier.query.filter_by(supplier_id=var2).first().suppliername
    updatedBalance = Supplier(supplierID, supplierName, DeductCommission, 'NOW()')
    db.session.merge(updatedBalance)
    db.session.commit()
    return str(DeductCommission)


@app.route('/RetrieveCommissionSupplier', methods=['GET', 'POST'])
def RetrieveCommission():
 if request.method == 'POST':
    var1 = request.form['supplier_id']
    supplierID = var1
    RetrieveBalance = Supplier.query.filter_by(supplier_id=var1).first()
    #return str(RetrieveBalance)
    return jsonify(SupplierID=RetrieveBalance.supplier_id, SupplierName=RetrieveBalance.suppliername, Current_Balance_Commission=RetrieveBalance.commission, Created_On=RetrieveBalance.created_on)



# ###############################   DATASETS    #####################################
# ###############################               #####################################

# 1 - ADD RECORD

@app.route('/AddRecordDatasets', methods=['GET', 'POST'])
def AddRecordDatasets():
 if request.method == 'POST':
    newdatasets_id = request.form['datasets_id']
    newcustomer_id = request.form['customer_id']
    newdatasetsfilepath = request.form['datasetsfilepath']
    newcreated_on = request.form['created_on']
    datasets = Datasets(newdatasets_id, newcustomer_id, newdatasetsfilepath, newcreated_on)
    db.session.add(datasets)
    db.session.commit()
    print ("Record ADDED Successfully!")
    DatasetsRecord = Datasets.query.all()
    return jsonify(DatasetsRecord = Datasets.serialize_list(DatasetsRecord))


# 2 - EDIT RECORD

# 3 - DELETE RECORD

@app.route('/DeleteRecordDatasets', methods=['GET', 'POST'])
def DeleteRecordDatasets():
 if request.method == 'POST':
    var1 = request.form['datasets_id']
    datasetsID = var1
    DeleteRecord = Datasets.query.filter_by(datasets_id=var1).first()
    db.session.delete(DeleteRecord)
    db.session.commit()
    print ("Record DELETED Successfully!")
    DatasetsRecord = Datasets.query.all()
    return jsonify(DatasetsRecord = Datasets.serialize_list(DatasetsRecord))

# 4 - LIST RECORD
@app.route('/execute/<datasets_id>/DatasetsJsonify', methods=['GET', 'POST'])
def DisplayDatasetsInJsonifyMode(datasets_id):
    allDatasets = Datasets.query.filter_by(datasets_id=datasets_id).first()
    return jsonify(Datasets_ID_Id=allDatasets.datasets_id, Customer_ID=allDatasets.customer_id,
                   DatasetsFilePath=allDatasets.datasetsfilepath, Created_On=allDatasets.created_on)


## 4.5 - QUERY RECORD BY CUSTOMER ID FROM WEB FORM/POSTMAN
@app.route('/execute/DisplayQueryDatasetsJsonify.json', methods=['GET', 'POST'])
def DisplayQueryDatasetssInJsonifyMode():
 if request.method == 'POST':
    var1 = request.form['customer_id']
    allDatasets = Datasets.query.filter_by(customer_id=var1).all()
    return jsonify(allDatasets = Datasets.serialize_list(allDatasets))


# 5 - LIST ALL RECORDS
@app.route('/execute/AllDatasetsJsonify.json', methods=['GET', 'POST'])
def DisplayAllDatasetsInJasonifyMode():
    #dataset = Datasets.query.filter_by(datasets_id=datasets_id).first()
    allDatasets = Datasets.query.all()
    return jsonify(allDatasets = Datasets.serialize_list(allDatasets))

# 6 - UPLOAD DATASET
###
@app.route('/uploadData/<customer_id>', methods=['GET', 'POST'])
def upload_DataAndUpdateDatasetsTable(customer_id):
    if request.method == 'POST':
        file = request.files['file']
        customerID = customer_id
        filename = secure_filename(file.filename)
        if file and allowed_file(filename):
            # check if customer folder exists and create if not
            datasetfilepath = "/home/chiefai/production/customers/customer_" + str(customer_id) + "/data"
            if os.path.exists(os.path.join(datasetfilepath, filename)):
               raise "This file path already exists"
            else:
               os.makedirs(datasetfilepath)
               file.save(os.path.join(datasetfilepath, filename))
        datasetsID = Datasets.query.order_by(Datasets.datasets_id.desc()).first().datasets_id + 1
        datasets_table = Datasets(datasetsID, customerID, datasetfilepath , 'NOW()')
        db.session.add(datasets_table)
        db.session.commit()
        return redirect(url_for('uploaded_file', filename=filename))
    return '''
    <!doctype html>
    <title>Upload a new File</title>
    <h2>Please Upload your DATA HERE!! (Only DATA to be uploaded here)(please be reminded only files with the following file extesions can be accepted ['txt', 'csv', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])</h2>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
          <input type=submit value=Upload>
         <input type="button" value="Go back!" onclick="history.back()">
    </form>
    '''

@app.route('/showUploadedData/<filename>/', methods=['GET', 'POST'])
def uploaded_Data(filename):
    return render_template('UploadFile.html', filename=filename)

@app.route('/OnceDatasIsUploaded/<filename>')
def send_Data_UpdateDatasetsTable(filename):
        return send_from_directory(UPLOAD_FOLDER, filename)
###


# ###############################   EXECUTIONS   ####################################
# ###############################                ####################################

# 1 - INSERT/CREATE NEW RECORD

@app.route('/AddRecordExecution', methods=['GET', 'POST'])
def AddRecordExecution():
 if request.method == 'POST':
    newexecution_id = request.form['execution_id']
    newmodel_id = request.form['model_id']
    newcustomer_id = request.form['customer_id']
    newcreated_on = request.form['created_on']
    newresult = request.form['result']
    newcharged_credits = request.form['charged_credits']
    newcommission_earned_chiefai = request.form['commission_earned_chiefai']
    execution = Execution(newexecution_id, newmodel_id, newcustomer_id, newcreated_on, newresult, newcharged_credits, newcommission_earned_chiefai)
    db.session.add(execution)
    db.session.commit()
    print ("Record ADDED Successfully!")
    ExecutionsRecord = Execution.query.all()
    return jsonify(ExecutionsRecord = Execution.serialize_list(ExecutionsRecord))


# 2 - EDIT RECORD

# 3 - DELETE RECORD

@app.route('/DeleteRecordExecution', methods=['GET', 'POST'])
def DeleteRecordExecution():
 if request.method == 'POST':
    var1 = request.form['execution_id']
    executionID = var1
    DeleteRecord = Execution.query.filter_by(execution_id=var1).first()
    db.session.delete(DeleteRecord)
    db.session.commit()
    print ("Record DELETED Successfully!")
    ExecutionRecord = Execution.query.all()
    return jsonify(ExecutionRecord = Execution.serialize_list(ExecutionRecord))


# 4 - LIST RECORD

@app.route('/execute/<execution_id>/ExecutionsJsonify', methods=['GET', 'POST'])
def DisplayExecutionsInJsonifyMode(execution_id):
    ExecutionID = Execution.query.filter_by(execution_id=execution_id).first().execution_id
    ModelID = Execution.query.filter_by(execution_id=execution_id).first().model_id
    CustomerID = Execution.query.filter_by(execution_id=execution_id).first().customer_id
    TimeStamp = Execution.query.filter_by(execution_id=execution_id).first().created_on
    ExecutionResult = Execution.query.filter_by(execution_id=execution_id).first().result
    ChargedCredits = Execution.query.filter_by(execution_id=execution_id).first().charged_credits
    CommissionEarnedChiefai = Execution.query.filter_by(execution_id=execution_id).first().commission_earned_chiefai
    allExecutions = Execution(ExecutionID, ModelID, CustomerID, TimeStamp, ExecutionResult, ChargedCredits,
                              CommissionEarnedChiefai)
    # return str(CommissionEarnedChiefai)
    # return jsonify(allExecutions = Execution.serialize_list(allExecutions))
    return jsonify(Execution_ID=allExecutions.execution_id, Model_ID=allExecutions.model_id,
                   Customer_ID=allExecutions.customer_id, Created_On=allExecutions.created_on,
                   Results=allExecutions.result, ChargedCredits=allExecutions.charged_credits,
                   CommissionEarnedChiefai=allExecutions.commission_earned_chiefai)


## 4.5 - QUERY RECORD BY CUSTOMER ID FROM WEB FORM/POSTMAN

@app.route('/execute/DisplayQueryExecutionsJsonify.json', methods=['GET', 'POST'])
def DisplayQueryExecutionsInJsonifyMode():
 if request.method == 'POST':
    var1 = request.form['customer_id']
    allExecutions = Execution.query.filter_by(customer_id=var1).all()
    return jsonify(allExecutions = Execution.serialize_list(allExecutions))

# 5 - LIST ALL RECORDS
@app.route('/execute/AllExecutionsJsonify.json', methods=['GET', 'POST'])
def DisplayAllExecutionsInJsonifyMode():
    allExecutions = Execution.query.all()
    return jsonify(allExecutions=Execution.serialize_list(
        allExecutions))  #### Here in the Execution Table the result column has a decimal point therefore we had to def an ENCODER as a global setting at the top ####

@app.route('/ExecutionsJsonify', methods=['GET', 'POST'])
def DisplayAllExecutionsInJasonifyModeUsingRawSQL():
    with engine.connect() as con:
        rs = con.execute("SELECT * FROM execution")
        # return jsonify(json_list = rs.all())
        return json.dumps([dict(r) for r in rs], cls=DecimalEncoder)
        fo = open("/home/chiefai/production/results/JsonDumpFile.json", 'w')
        filebuffer = JsonDumpFile
        fo.writelines(filebuffer)
        SaveTextFile = filebuffer
        fo.close()


# ###############################  COMPLEX EXECUTIONS for running model  ####################################
# ###############################                                        ####################################

# 1 - non-zipped files

# Upload model, executor script and test image for prediction
# Executes model
# Charges credits to Customer, and adds commission to Supplier
# Saves model execution
# Updates all relevant tables

###
@app.route('/executeModelAndChargeCreditsAndUpdateCustomerAndSupplierTable', methods=['GET', 'POST'])
def executeModelAndChargeCreditsAndUpdateCustomerSupplierTable():
    if request.method == 'POST':
        var1 = request.form['model_id']
        var2 = request.form['modelname']
        ## modelpath has been sperately defined ##
        var4 = request.form['supplier_id']
        var5 = request.form['customer_id']
        var6 = request.form['created_on']
        var7 = request.form['last_login']
        var8 = request.form['price']
        supplierID = var4
        customerID = var5

    if request.method == 'POST':
        # check if the post request has the file part
        if 'fileC' not in request.files:
            flash('No file part')
            return redirect(request.url)
        fileC = request.files['fileC']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        filenameC = secure_filename(fileC.filename)
        if fileC and allowed_file(filenameC):
            Data_dir = "/home/chiefai/production/customers/customer_" + str(
                var5) + "/data"  # check if model folder exist$
            DataPath = os.path.join(Data_dir, filenameC)
            if os.path.exists(DataPath):
                raise Exception('An error occurred Data Path exists')
            else:
                os.makedirs(Data_dir,
                            exist_ok=True)  # In this line os.makedirs("path/to/directory", exist_ok=True) makes it accept multiple files in the same directory or foler (i.e in our case /production/customer_"Whatever custome$
                fileC.save(DataPath)
        else:
            raise Exception('An error occurred Data Dir exists or . filename extension is WRONG....!!!!')

    if request.method == 'POST':
        # check if the post request has the file part
        if 'fileB' not in request.files:
            flash('No file part')
            return redirect(request.url)
        fileA = request.files['fileA']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        filenameA = secure_filename(fileA.filename)
        if fileA and allowed_file(filenameA):
            executor_dir = "/home/chiefai/production/suppliers/supplier_" + str(
                var4) + "/executor"  # check if model folder exist$
            executorPath = os.path.join(executor_dir, filenameA)
            if os.path.exists(executorPath):
                raise Exception('An error occurred Executor Path exists')
            else:
                os.makedirs(executor_dir,
                            exist_ok=True)  # In this line os.makedirs("path/to/directory", exist_ok=True) makes it accept multiple files in the same directory or foler (i.e in our case /production/customer_"Whatever custome$
                fileA.save(executorPath)
        else:
            raise Exception('An error occurred Executor Dir exists or . filename extension is WRONG....!!!!')

    if request.method == 'POST':
        # check if the post request has the file part
        if 'fileA' not in request.files:
            flash('No file part')
            return redirect(request.url)
        fileB = request.files['fileB']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        filenameB = secure_filename(fileB.filename)
        if fileB and allowed_file(filenameB):
            model_dir = "/home/chiefai/production/suppliers/supplier_" + str(
                var4) + "/models"  # check if model folder exist$
            modelPath = os.path.join(model_dir, filenameB)
            if os.path.exists(modelPath):
                raise Exception('An error occurred Model Path exists')
            else:
                os.makedirs(model_dir,
                            exist_ok=True)  # In this line os.makedirs("path/to/directory", exist_ok=True) makes it accept$
                fileB.save(modelPath)
        else:
            raise Exception('An error occurred Model Dir exists or . filename extension is WRONG....!!!!')

        models_table = Models(var1, var2, executorPath, modelPath, var4, var6, var7, var8)
        db.session.add(models_table)
        db.session.commit()

        A = Customer.query.filter_by(customer_id=var5).first().credits
        B = Models.query.filter_by(modelname=var2).first().price
        C = Supplier.query.filter_by(supplier_id=var4).first().commission
        D = A - B

        E = (
            70 * B) / 100  #### Percentage calculation - 70% goes to Supplier, so 14 credits (which is 70% of 20 credits) is added to the Supplier Table ####
        F = (
            30 * B) / 100  #### Percentage calculation - 30% goes to Chief AI, so  7 credits (which is 30% of 20 credits) is added to the Execution Table ####

        G = C + E  #### G contains the ADDED commission in percentage converted to credits to the Supplier Credits Earned ####

        balanceMinusCustomer = D
        balanceAddSupplier = G

        customerName = Customer.query.filter_by(customer_id=var5).first().customername
        updatedBalanceCustomer = Customer(customerID, customerName, balanceMinusCustomer, 'NOW()')
        db.session.merge(updatedBalanceCustomer)
        db.session.commit()
        supplierName = Supplier.query.filter_by(supplier_id=var4).first().suppliername
        updatedBalanceSupplier = Supplier(supplierID, supplierName, balanceAddSupplier, 'NOW()')
        db.session.merge(updatedBalanceSupplier)
        db.session.commit()

        # model_path = Models.query.filter_by(modelname=var2).first().modelpath
        # result = main(var9, var10, var11, model_path=model_path)
        # float(result)
        model_path = Models.query.filter_by(modelname=var2).first().modelpath
        result = couture_execute(model_path=model_path, img_path=DataPath)

        datasetsID = Datasets.query.order_by(Datasets.datasets_id.desc()).first().datasets_id + 1
        datasets_table = Datasets(datasetsID, customerID, DataPath, 'NOW()')
        db.session.add(datasets_table)
        db.session.commit()

        model_id = Models.query.filter_by(modelname=var2).first().model_id
        customer_id = Customer.query.filter_by(customer_id=var5).first().customer_id
        execute_id = Execution.query.order_by(Execution.execution_id.desc()).first().execution_id + 1
        chargedCredits = B
        commission_Earned_Chiefai = F

        saveIntoExecutionTable = Execution(execute_id, model_id, customer_id, 'NOW()', result, chargedCredits,
                                           commission_Earned_Chiefai)

        fo = open("/home/chiefai/production/results/chargedCreditsAfterUploading.txt", 'w')
        filebuffer = "PREDICTION RESULT : " + str(result) + "\n" + "Customer Balace : " + str(
            balanceMinusCustomer) + "\n" + "Supplier Balance : " + str(
            balanceAddSupplier) + "\n" + "Credits Earned by Chief AI : " + str(F)
        fo.writelines(filebuffer)
        SaveTextFile = filebuffer
        fo.close()
        #   return jsonify(result)

        db.session.add(saveIntoExecutionTable)
        db.session.commit()

        #   #return render_template('mainResultDisplay.html', myExecution=saveOutput, myCustomer=customer_name)
        # return str(filebuffer)

        return redirect(url_for('uploaded_data_modelExecuteAndUpdate', filenameC=filenameC, filenameA=filenameA,
                                filenameB=filenameB))
        # return ("done")
    return '''
 <!doctype html>
 <title>Upload a new Model File Path</title>
 <h2>Please Upload your File (please be reminded only files with the following file extesions can be accepted ['txt', 'csv', 'pdf', 'png', 'jpg', 'jpeg', 'tif', 'tiff', 'gif', 'h5', 'pkl', 'py'])</h2>
 <form action="" method=post enctype=multipart/form-data>
 <p>ModelID: <input type=text name=model_id></p>
 <p>ModelName: <input type=text name=modelname></p>
 <p>SupplierID: <input type=text name=supplier_id></p>
 <p>CustomerID: <input type=number name=customer_id></p>
 <p>Created_On: <input type=date name=created_on></p>
 <p>Last_Login: <input type=date name=last_login></p>
 <p>Price: <input type=number name=price></p>
 <p>Upload an Image File [should be a '.png' or '.jpg' or '.jpeg' or '.tif' or '.tiff' or '.gif']: <input type=file name=fileC></p>
   <p>Upload Model Executor Script [should be a '.py'(Python file)]: <input type=file name=fileA></p>
   <p>Upoad a Model (.h5 or .pkl file): <input type=file name=fileB></p>
       <input type=submit value=Upload></p>
       <input type="button" value="Go back!" onclick="history.back()">
 </form>
 <head>
   <!-- START of the HIGH CHART Section -->
   <script src="https://code.highcharts.com/highcharts.js"></script>
   <script src="https://code.highcharts.com/modules/data.js"></script>
   <script src="https://code.highcharts.com/js/themes/dark-unica.js"></script>
   <!--END of the HIGH CHART Section API-->

   <!--Load the AJAX API-->
   <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
   <script type="text/javascript">

    // Load the Visualization API and the corechart package.
    google.charts.load('current', {'packages':['corechart']});

    // Set a callback to run when the Google Visualization API is loaded.
    google.charts.setOnLoadCallback(drawChart);

    // Callback that creates and populates a data table,
    // instantiates the pie chart, passes in the data and
    // draws it.
    function drawChart() {

       // Create the data table.
      var data = new google.visualization.DataTable();
      data.addColumn('string', 'Topping');
      data.addColumn('number', 'Slices');
      data.addRows([
        ['Models Table', 3],
        ['Customer Table', 1],
        ['Supplier Table', 1],
        ['Datasets Table', 1],
        ['Executions Table', 2]
      ]);

      // Set chart options
      var options = {'title':'Table Sizes Ratio',
                     'width':400,
                     'height':300};

      // Instantiate and draw our chart, passing in some options.
      var chart = new google.visualization.PieChart(document.getElementById('chart_div'));
      chart.draw(data, options);
    }
    <!--END OF THE GOOGLE CHARTS Section-->
  </script>

  <style>
  .ld-label {
          width:200px;
          display: inline-block;
  }

  .ld-row {
  }

  .ld-url-input {
          width: 500px;
  }

  .ld-time-input {
          width: 40px;
  }
  </style>
  </head>

  <body>
    <!-- START of the HIGH CHART Section -->
    <div id="container" style="min-width: 310px; height: 400px; margin: 0 auto"></div>
    <!--END OF THE HIGH CHARTS Section-->

    <!--Div that will hold the pie chart-->
   <!--  <div id="chart_div"></div> -->
  </body>

  <div class="ld-row">
          <label class="ld-label">
                  Enable Polling
          </label>
          <input type="checkbox" checked="checked" id="enablePolling"/>
  </div>
  <div class="ld-row">
          <label class="ld-label">
                  Polling Time (Seconds)
          </label>
          <input class="ld-time-input" type="number" value="2" id="pollingTime"/>
  </div>
  <div class="ld-row">
          <label class="ld-label">
                  CSV URL
          </label>
          <input class="ld-url-input" type="text" id="fetchURL"/>
  </div>
  <script>
  var defaultData = 'https://demo-live-data.highcharts.com/time-data.csv';
  var urlInput = document.getElementById('fetchURL');
  var pollingCheckbox = document.getElementById('enablePolling');
  var pollingInput = document.getElementById('pollingTime');

  function createChart() {
      Highcharts.chart('container', {
          chart: {
              type: 'spline'
          },
          title: {
              text: 'Live Data'
          },
          data: {
              csvURL: urlInput.value,
              enablePolling: pollingCheckbox.checked === true,
              dataRefreshRate: parseInt(pollingInput.value, 10)
          }
      });

      if (pollingInput.value < 1 || !pollingInput.value) {
          pollingInput.value = 1;
      }
  }

  urlInput.value = defaultData;

  // We recreate instead of using chart update to make sure the loaded CSV
  // and such is completely gone.
  pollingCheckbox.onchange = urlInput.onchange = pollingInput.onchange = createChart;

  // Create the chart
  createChart();
  </script>
  <body>
  <div id="chart_div"></div>
  </body>
 '''

@app.route('/showUploadedDataModelAndExecuteAndUpdate/<filenameC>/<filenameA>/<filenameB>',
           methods=['GET', 'POST'])
def uploaded_data_modelExecuteAndUpdate(filenameC, filenameA, filenameB):
    return render_template('UploadDataModelAndExecutorAndUpdate.html', filenameC=filenameC, filenameA=filenameA,
                           filenameB=filenameB)

@app.route('/OncefileisIsUploadedAndExecuteAndUpdate/<filenameC>/<filenameA>/<filenameB>')
def send_data_modelExecuteAndUpdate(filenameC, filenameA, filenameB):
    return send_from_directory(UPLOAD_FOLDER, filename)
###

######
######


# 2 - latest endpoint

# Accepts model & executor scripts as a zipped file
# Unzip model, executor script
# Upload test image for prediction
# Executes model
# Charges credits to Customer, and adds commission to Supplier
# Saves model execution
# Updates all relevant tables


@app.route('/executeZippedAndChargeCreditsAndUpdateCustomerAndSupplierTable', methods=['GET', 'POST'])
def executeZippedAndChargeCreditsAndUpdateCustomerSupplierTable():
 if request.method == 'POST':
    var1 = request.form['model_id']
    var2 = request.form['modelname'] ########## var2 must be the name of the original directory which was zipped ###########
    ## modelpath has been separately defined ##
    var4 = request.form['supplier_id']
    var5 = request.form['customer_id']
    var6 = request.form['created_on']
    var7 = request.form['last_login']
    var8 = request.form['price']
    supplierID = var4
    customerID = var5

 if request.method == 'POST':
    # check if the post request has the file part
    if 'fileA' not in request.files:
        flash('No file part')
        return redirect(request.url)
    fileA = request.files['fileA']
    # if user does not select file, browser also
    # submit a empty part without filename
    if fileA.filename == '':
       flash('No selected file')
       return redirect(request.url)
    filenameA = secure_filename(fileA.filename)
    if fileA and allowed_file(filenameA):
        Data_dir = "/home/chiefai/production/customers/customer_" + str(var5) + "/data" # check if model folder exist#
        DataPath = os.path.join(Data_dir, filenameA)
        if os.path.exists(DataPath):
            raise Exception('An error occurred Data Path exists')
        else:
            os.makedirs(Data_dir, exist_ok=True) # In this line os.makedirs("path/to/directory", exist_ok=True) makes it accept multiple files in the same directory or foler (i.e in our case /production/customer_"Whatever custome$
            fileA.save(DataPath)
    else: raise Exception('An error occurred Data Dir exists or . filename extension is WRONG....!!!!')

 if request.method == 'POST':
    # check if the post request has the file part
    if 'fileB' not in request.files:
        flash('No file part')
        return redirect(request.url)
    fileB = request.files['fileB']
    # if user does not select file, browser also
    # submit a empty part without filename
    if fileB.filename == '':
       flash('No selected file')
       return redirect(request.url)
    filenameB = secure_filename(fileB.filename)
    if fileB and allowed_file(filenameB):
        executor_dir = "/home/chiefai/production/suppliers/supplier_" + str(var4) + "/executorFolder/" # check if model folder exist #
        executorPath = os.path.join(executor_dir, filenameB) # path to zipped model folder
        if os.path.exists(executorPath):
            raise Exception('An error occurred Executor Path exists')
        else:
            os.makedirs(executor_dir, exist_ok=True) # In this line os.makedirs("path/to/directory", exist_ok=True) makes it accept multiple files in the same directory or foler (i.e in our case /production/supplier_"Whatever supplier
            fileB.save(executorPath)
            zip_ref = zipfile.ZipFile(os.path.join(executor_dir, filenameB), 'r')
            zip_ref.extractall(executor_dir)
            zip_ref.close()
    else: raise Exception('An error occurred Executor Dir exists or . filename extension is WRONG....!!!!')
    unzip_dir = os.path.join(executor_dir, var2)
    exec_file_path = os.path.join(unzip_dir, "executor.py") # path to executor file
    models_table = Models(var1, var2, exec_file_path, unzip_dir, var4, var6, var7, var8)
    db.session.add(models_table)
    db.session.commit()

    A = Customer.query.filter_by(customer_id=var5).first().credits
    B = Models.query.filter_by(modelname=var2).first().price
    C = Supplier.query.filter_by(supplier_id=var4).first().commission
    D = A - B

    E = (70*B)/100 #### Percentage calculation - 70% goes to Supplier, so 14 credits (which is 70% of 20 credits) is added to the Supplier Table ####
    F = (30*B)/100 #### Percentage calculation - 30% goes to Chief AI, so  7 credits (which is 30% of 20 credits) is added to the Execution Table ####

    G = C + E #### G contains the ADDED commission in percentage converted to credits to the Supplier Credits Earned ####

    balanceMinusCustomer = D
    balanceAddSupplier = G

    customerName = Customer.query.filter_by(customer_id=var5).first().customername
    updatedBalanceCustomer = Customer(customerID, customerName, balanceMinusCustomer, 'NOW()')
    db.session.merge(updatedBalanceCustomer)
    db.session.commit()
    supplierName = Supplier.query.filter_by(supplier_id=var4).first().suppliername
    updatedBalanceSupplier = Supplier(supplierID, supplierName, balanceAddSupplier, 'NOW()')
    db.session.merge(updatedBalanceSupplier)
    db.session.commit()

    ####################
    # MODEL EXECUTION
    ####################

    #### import execute function from MODEL-SPECIFIC executor file
    ### var2 = name of the extracted model folder

    model_name = var2

    sys.path.append(executor_dir)
    sys.path.append(os.path.join(executor_dir, model_name))

    module = importlib.import_module(".executor", model_name)
    result = module.execute(DataPath)


    datasetsID = Datasets.query.order_by(Datasets.datasets_id.desc()).first().datasets_id + 1
    datasets_table = Datasets(datasetsID, customerID, DataPath , 'NOW()')
    db.session.add(datasets_table)
    db.session.commit()

    model_id = Models.query.filter_by(modelname=var2).first().model_id
    customer_id = Customer.query.filter_by(customer_id=var5).first().customer_id
    execute_id = Execution.query.order_by(Execution.execution_id.desc()).first().execution_id + 1
    chargedCredits = B
    commission_Earned_Chiefai = F

    saveIntoExecutionTable = Execution(execute_id, model_id, customer_id, 'NOW()', result, chargedCredits, commission_Earned_Chiefai)

    fo = open("/home/chiefai/production/results/chargedCreditsAfterUploading.txt", 'w')
    filebuffer = "PREDICTION RESULT : " + str(result) + "\n" + "Customer Balace : " + str(balanceMinusCustomer) + "\n" + "Supplier Balance : " + str(balanceAddSupplier) + "\n" + "Credits Earned by Chief AI : " + str(F)
    fo.writelines(filebuffer)
    SaveTextFile = filebuffer
    fo.close()
#   return jsonify(result)

    db.session.add(saveIntoExecutionTable)
    db.session.commit()

#   #return render_template('mainResultDisplay.html', myExecution=saveOutput, myCustomer=customer_name)
    #return str(filebuffer)

    return redirect(url_for('uploaded_Zipped_ExecuteAndUpdate', filenameA=filenameA, filenameB=filenameB))
    #return ("done")
 return '''
 <!doctype html>
 <title>Upload a new Model File Path</title>
 <h2>Please Upload your File (please be reminded only files with the following file extesions can be accepted ['png', 'jpg', 'jpeg', 'tif', 'tiff', 'gif', 'zip'])</h2>
 <form action="" method=post enctype=multipart/form-data>
 <p>ModelID: <input type=text name=model_id></p>
 <p>ModelName: <input type=text name=modelname></p>
 <p>SupplierID: <input type=text name=supplier_id></p>
 <p>CustomerID: <input type=number name=customer_id></p>
 <p>Created_On: <input type=date name=created_on></p>
 <p>Last_Login: <input type=date name=last_login></p>
 <p>Price: <input type=number name=price></p>
 <p>Upload an Image File [should be a '.png' or '.jpg' or '.jpeg' or '.tif' or '.tiff' or '.gif']: <input type=file name=fileA></p>
 <p>Upload Model Executor Script [should be a ('.ZIP') file]: <input type=file name=fileB></p>
     <input type=submit value=Upload_&_Execute></p>
     <input type="button" value="Go back!" onclick="history.back()">
 </form>
 <head>
   <!-- START of the HIGH CHART Section -->
   <script src="https://code.highcharts.com/highcharts.js"></script>
   <script src="https://code.highcharts.com/modules/data.js"></script>
   <script src="https://code.highcharts.com/js/themes/dark-unica.js"></script>
   <!--END of the HIGH CHART Section API-->

   <!--Load the AJAX API-->
   <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
   <script type="text/javascript">

    // Load the Visualization API and the corechart package.
    google.charts.load('current', {'packages':['corechart']});

    // Set a callback to run when the Google Visualization API is loaded.
    google.charts.setOnLoadCallback(drawChart);

    // Callback that creates and populates a data table,
    // instantiates the pie chart, passes in the data and
    // draws it.
    function drawChart() {

       // Create the data table.
      var data = new google.visualization.DataTable();
      data.addColumn('string', 'Topping');
      data.addColumn('number', 'Slices');
      data.addRows([
        ['Models Table', 3],
        ['Customer Table', 1],
        ['Supplier Table', 1],
        ['Datasets Table', 1],
        ['Executions Table', 2]
      ]);

      // Set chart options
      var options = {'title':'Table Sizes Ratio',
                     'width':400,
                     'height':300};

      // Instantiate and draw our chart, passing in some options.
      var chart = new google.visualization.PieChart(document.getElementById('chart_div'));
      chart.draw(data, options);
    }
    <!--END OF THE GOOGLE CHARTS Section-->
  </script>

  <style>
  .ld-label {
          width:200px;
          display: inline-block;
  }

  .ld-row {
  }

  .ld-url-input {
          width: 500px;
  }

  .ld-time-input {
          width: 40px;
  }
  </style>
  </head>

  <body>
    <!-- START of the HIGH CHART Section -->
    <div id="container" style="min-width: 310px; height: 400px; margin: 0 auto"></div>
    <!--END OF THE GOOGLE CHARTS Section-->

    <!--Div that will hold the pie chart-->
   <!--  <div id="chart_div"></div> -->
  </body>

  <div class="ld-row">
          <label class="ld-label">
                  Enable Polling
          </label>
          <input type="checkbox" checked="checked" id="enablePolling"/>
  </div>
  <div class="ld-row">
          <label class="ld-label">
                  Polling Time (Seconds)
          </label>
          <input class="ld-time-input" type="number" value="2" id="pollingTime"/>
  </div>
  <div class="ld-row">
          <label class="ld-label">
                  CSV URL
          </label>
          <input class="ld-url-input" type="text" id="fetchURL"/>
  </div>
  <script>
  var defaultData = 'https://demo-live-data.highcharts.com/time-data.csv';
  var urlInput = document.getElementById('fetchURL');
  var pollingCheckbox = document.getElementById('enablePolling');
  var pollingInput = document.getElementById('pollingTime');

  function createChart() {
      Highcharts.chart('container', {
          chart: {
              type: 'spline'
          },
          title: {
              text: 'Live Data'
          },
          data: {
              csvURL: urlInput.value,
              enablePolling: pollingCheckbox.checked === true,
              dataRefreshRate: parseInt(pollingInput.value, 10)
          }
      });

      if (pollingInput.value < 1 || !pollingInput.value) {
          pollingInput.value = 1;
      }
  }

  urlInput.value = defaultData;

  // We recreate instead of using chart update to make sure the loaded CSV
  // and such is completely gone.
  pollingCheckbox.onchange = urlInput.onchange = pollingInput.onchange = createChart;

  // Create the chart
  createChart();
  </script>
  <body>
  <div id="chart_div"></div>
  </body>
 '''

@app.route('/showUploadedZippedFolderAndExecuteAndUpdate/<filenameA>/<filenameB>', methods=['GET', 'POST'])
def uploaded_Zipped_ExecuteAndUpdate(filenameA, filenameB):
    return render_template('UploadZippedExecutorAndUpdate.html', filenameA=filenameA, filenameB=filenameB)

@app.route('/OnceZippedFolderisUploadedAndExecuteAndUpdate/<filenameA>/<filenameB>')
def send_Zipped_ExecuteAndUpdate(filenameA, filenameB):
        return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == '__main__':
    #reload(sys)
    #sys.setdefaultencoding('utf-8')
    app.run(host='0.0.0.0', port=5000, debug=True)


