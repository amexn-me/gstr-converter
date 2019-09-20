from flask import Flask, render_template, request, jsonify, send_file
from werkzeug import secure_filename
import json
import pandas as pd 
from pandas.io.json import json_normalize
import os, sys

ALLOWED_EXTENSIONS = set(['json'])
app = Flask(__name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("gstr-1.html")

@app.route("/generate", methods = ["GET", "POST"])
def upload_file():
    if request.method == 'POST':
      f = request.files['file']
      if f and allowed_file(f.filename):
          filename = secure_filename(f.filename)
          f.save(filename)
          os.rename(filename, "input.json")
      else:
          return render_template("gstr-1.html")
      return render_template("generate.html")
    
@app.route("/download", methods = ["GET", "POST"])
def generate():
    with open('input.json') as f:
        d = json.load(f)


    #Extracting B2B Invoices
    tempb2b = json_normalize(d, 'b2b')
    b2binv = pd.DataFrame()
    for i, row in tempb2b.iterrows():
        data = row['inv']
        b2binv = b2binv.append(data)
    b2binv.rename(columns={'idt':'Invoice Date',
                          'inum':'Invoice Number',
                          'val':'Invoice Value',
                          'inv_typ':'Invoice Type'},
                 inplace=True)
    b2bheader = ["Invoice Date", "Invoice Number", "Invoice Value", "Invoice Type"]
    
    #Extracting B2C Invoices
    b2cinv = pd.DataFrame()
    b2cinv = json_normalize(d, 'b2cs')
    b2cinv.rename(columns={'txval':'Total Taxable Value',
                          'rt':'Tax Rate',
                          'camt':'CGST',
                          'samt': 'SGST'},
                 inplace=True)
    b2cheader = ["Total Taxable Value", "Tax Rate", "CGST", "SGST"]


    #Extracting Credit and Debit Notes
    tempcdnr = json_normalize(d, 'cdnr')
    cdnrinv = pd.DataFrame()
    for i, row in tempcdnr.iterrows():
        data = row['nt']
        cdnrinv = cdnrinv.append(data)
    cdnrinv.rename(columns={'idt':'Invoice Date',
                          'inum':'Invoice Number',
                          'val':'Invoice Value',
                          'ntty': 'Note Type',
                          'nt_dt':'Credit/Debit Note Date'},
                 inplace=True)
    cdnrheader = ["Invoice Date", "Invoice Number", "Invoice Value", "Note Type", "Credit/Debit Note Date"]

    with pd.ExcelWriter('output.xlsx') as writer:
        b2binv.to_excel(writer, columns = b2bheader, sheet_name='B2B', index=False)
        cdnrinv.to_excel(writer, columns = cdnrheader, sheet_name='CDNR', index=False)
        b2cinv.to_excel(writer, columns = b2cheader, sheet_name='B2C', index=False)

    return render_template("download.html")

@app.route('/xlsx_output') # this is a job for GET, not POST
def xlsx_output():
    return send_file("output.xlsx",
                     mimetype='text/xlsx',
                     attachment_filename="output.xlsx",
                     as_attachment=True,
                     cache_timeout=-1)

@app.route("/gstr-3b")
def gstr3b():
    return render_template("gstr-3b.html")