import pyrebase
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
from bs4 import BeautifulSoup
import re
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
from flask import make_response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
from io import StringIO
import csv


cred = credentials.Certificate('firebase/serviceaccountkey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://cnctfirebasrtopy-default-rtdb.firebaseio.com"
})

#firebase config
config = {
  "apiKey": "AIzaSyDzCxEcjKLOfsDoFSsHwVc0ZSPi6MnuDAI",
  "authDomain": "cnctfirebasrtopy.firebaseapp.com",
  "databaseURL": "https://cnctfirebasrtopy-default-rtdb.firebaseio.com",
  "projectId": "cnctfirebasrtopy",
  "storageBucket": "cnctfirebasrtopy.appspot.com",
  "messagingSenderId": "84687946449",
  "appId": "1:84687946449:web:0a476ef01a3495460c7bf0",
  "measurementId": "G-20TMTEEKL7"
}




#initialising firebasedatabase --- 
firebase = pyrebase.initialize_app(config)
database = firebase.database()
database = db.reference()

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
auth=firebase.auth()


 
@app. route('/',methods=['GET','POST'])
def index():
    if request.method=='POST':
        email=request.form['email']
        password=request.form[ 'password']
        try:
            user=auth.sign_in_with_email_and_password(email,password)
            return render_template('home_page.html')
        except:
            return render_template('index.html')
    return render_template('index.html')


@app.route('/home_page',methods=['GET','POST'])
def home_page():
    return render_template('home_page.html')
    
    
    
@app.route('/reset' ,methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        email=request.form['email']
        auth.send_password_reset_email(email)
        return redirect(url_for('index'))
    return render_template('reset.html')
   
 


@app.route('/url',methods=('GET','POST'))
def url():
    if request.method == 'POST':
        accesed_url = request.form['urll']
        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.get(accesed_url)

        # keep clicking show more
        while True:
            try:
                btn = driver.find_element("id","gsc_bpf_more")
                if not btn.is_enabled():
                    break
                btn.click()
                print("btn clicked")
                time.sleep(2)
            except NoSuchElementException:
                break
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        table = soup.find('table', id='gsc_a_t')
        tr= table.find_all('tr',class_='gsc_a_tr')
        for i in tr:
            title_name=i.find('a',class_='gsc_a_at').text
            title_name=title_name.replace('"','')
            title=re.sub(r'\W+', '', title_name).replace(' ', '_')
            details=i.find_all('div',class_='gs_gray')
            loop_count = 0
            for n,j in enumerate(details):
                if n==0:
                    authors=j.text
                    
                else:
                    publication=j.text
            y=i.find('span',class_='gsc_a_h gsc_a_hc gs_ibl')
            c=i.find('a',class_='gsc_a_ac gs_ibl')
            publication=publication.split(',')[0]
            year=y.text
            cited_by=c.text
                    
            key=title+year
            

            if authors.endswith('...'):
                authors = authors[:-3]  # remove the last three characters from the string
            authors_list = authors.split(',')
            if authors_list[-1]==" ":  # check if the last item starts with a space
                authors_list.pop()  # remove the last item from the list
            
            authors = authors_list

            if authors:
                author_names = authors
                non_empty_authors = [author.strip() for author in author_names if author.strip()]
                if non_empty_authors:
                    database.child("Publications").child(key).update({'title':title_name,'year':year,'cited_by':cited_by})
                    database.child("Publications").child(key).child("publication").update({'publication':publication,'p_tagg':"untagged"})
                    database.child("Publications").child(key).update({"SCI":0,"Scopus":0,"tagg":"untagged"})
                    for author in non_empty_authors:
                        database.child("Publications").child(key).child("authors").child(author).update({'name':author,'tagg':"untagged"})
                    

        return redirect(url_for('home_page'))
    
    return render_template('url.html')
    
 
 
 
    
@app.route('/search' ,methods=['GET' , 'POST'])
def search():
    if request.method == 'POST':
        
   
        author_name0=request.form.get('author')
        author_name=author_name0.lower()
        year=request.form.get('year')
        to_year=request.form.get('to_year')
        from_year=request.form.get('from_year')
        p_tagg=request.form.get('p_tagg')
        tagg=request.form.get('tagg')
        sci=request.form.get('sci') == 'true'
        scopus=request.form.get('scopus')  == 'true'

        if not year:
            year='all'
        if not from_year:
            from_year='all'
        if not to_year:
            to_year='all'
        if not author_name:
            author_name='all'
        if not tagg:
            tagg='all'
        if not p_tagg:
            p_tagg='all'
        
        
        if not sci and not scopus:
            sci_scopus=0
            print("0")
        elif sci and scopus:
            sci_scopus=1
            print("1")
        else:
            print("2")
            sci_scopus=2
            
        publications_ref = database.child('Publications')
        publications = publications_ref.get()
        result={}
        if str(to_year)!='all' and str(from_year)!='all':
            if to_year.isnumeric() and from_year.isnumeric():
                for key, publication in publications.items():
                    if sci_scopus==1:
                        if publication.get('SCI')==False or  publication.get('Scopus')==False:
                            continue
                    if sci_scopus==2:
                        if sci==True:
                            
                            if not publication.get('SCI')==sci:
                                continue
                        else:
                            if not publication.get('Scopus')==scopus:
                                continue

                    pub_year=publication.get('year')
                    if pub_year and to_year and int(pub_year)>=int(from_year) and int(pub_year)<=int(to_year):
                        if( (author_name == 'all' and tagg == 'all') ):
                            result[key]=publication
                        
                        elif author_name == 'all' and tagg == 'all':
                            if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                                result[key] = publication
                                
                        elif author_name == 'all' and p_tagg == 'all':
                            for author_key, author in publication.get('authors').items():
                                if author.get('tagg') == tagg:
                                    result[key]=publication
                                

                        elif tagg == 'all' and p_tagg == 'all':
                            for author_key, author in publication.get('authors').items():
                                temp = author.get('name').strip()
                                if author_name in temp.lower():
                                    result[key] = publication
                                

                        elif author_name == 'all':
                            if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                                for author_key, author in publication.get('authors').items():
                                    if author.get('tagg') == tagg:
                                        result[key] = publication
                                        
                        elif tagg == 'all':
                            if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                                for author_key, author in publication.get('authors').items():
                                    temp = author.get('name').strip()
                                    if author_name in temp.lower():
                                        result[key] = publication
                                    
                        
                        elif p_tagg == 'all':
                            for author_key, author in publication.get('authors').items():
                                temp = author.get('name').strip()
                                if author_name in temp.lower() and author.get('tagg') == tagg:
                                    result[key] = publication
            
        
        elif str(to_year)=='all' and str(from_year)!='all':
            
            for key, publication in publications.items():
                if sci_scopus==1:
                    if publication.get('SCI')==False or  publication.get('Scopus')==False:
                        continue
                if sci_scopus==2:
                    if sci==True:
                        if not publication.get('SCI')==sci:
                            continue
                    else:
                        if not publication.get('Scopus')==scopus:
                            continue
                pub_year=publication.get('year')
                if from_year.isnumeric() and from_year and pub_year and int(pub_year)>=int(from_year):
                    if( (author_name == 'all' and tagg == 'all') ):
                        result[key]=publication
                    
                    elif author_name == 'all' and tagg == 'all':
                        if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                            result[key] = publication
                            
                    elif author_name == 'all' and p_tagg == 'all':
                        for author_key, author in publication.get('authors').items():
                            if author.get('tagg') == tagg:
                                result[key]=publication
                            

                    elif tagg == 'all' and p_tagg == 'all':
                        for author_key, author in publication.get('authors').items():
                            temp = author.get('name').strip()
                            if author_name in temp.lower():
                                result[key] = publication
                            

                    elif author_name == 'all':
                        if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                            for author_key, author in publication.get('authors').items():
                                if author.get('tagg') == tagg:
                                    result[key] = publication
                                    
                    elif tagg == 'all':
                        if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                            for author_key, author in publication.get('authors').items():
                                temp = author.get('name').strip()
                                if author_name in temp.lower():
                                    result[key] = publication
                                
                    
                    elif p_tagg == 'all':
                        for author_key, author in publication.get('authors').items():
                            temp = author.get('name').strip()
                            if author_name in temp.lower() and author.get('tagg') == tagg:
                                result[key] = publication
            
        
        elif str(to_year)!='all' and str(from_year)=='all':
            if to_year.isnumeric() and to_year!='':
                for key, publication in publications.items():
                    if sci_scopus==1:

                        if publication.get('SCI')==False or  publication.get('Scopus')==False:
                            
                            continue
                    if sci_scopus==2:
                        if sci==True:
                            
                            if not publication.get('SCI')==sci:
                                continue
                        else:
                            if not publication.get('Scopus')==scopus:
                                continue
                    pub_year=publication.get('year')
                    if pub_year and int(pub_year)<=int(to_year):
                        if( (author_name == 'all' and tagg == 'all') ):
                            result[key]=publication
                        
                        elif author_name == 'all' and tagg == 'all':
                            if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                                result[key] = publication
                                
                        elif author_name == 'all' and p_tagg == 'all':
                            for author_key, author in publication.get('authors').items():
                                if author.get('tagg') == tagg:
                                    result[key]=publication
                                

                        elif tagg == 'all' and p_tagg == 'all':
                            for author_key, author in publication.get('authors').items():
                                temp = author.get('name').strip()
                                if author_name in temp.lower():
                                    result[key] = publication
                                

                        elif author_name == 'all':
                            if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                                for author_key, author in publication.get('authors').items():
                                    if author.get('tagg') == tagg:
                                        result[key] = publication
                                        
                        elif tagg == 'all':
                            if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                                for author_key, author in publication.get('authors').items():
                                    temp = author.get('name').strip()
                                    if author_name in temp.lower():
                                        result[key] = publication
                                    
                        
                        elif p_tagg == 'all':
                            for author_key, author in publication.get('authors').items():
                                temp = author.get('name').strip()
                                if author_name in temp.lower() and author.get('tagg') == tagg:
                                    result[key] = publication
            
        
        for key, publication in publications.items():
            if sci_scopus==1:
                
                if publication.get('SCI')==False or  publication.get('Scopus')==False:
                    
                    continue
                
            elif sci_scopus==2:
                if sci==True:
                    if not publication.get('SCI')==sci:
                        continue
                else:
                    if not publication.get('Scopus')==scopus:
                        continue
            if str(year) == 'all' and str(from_year)=='all' and str(to_year)=='all':
                if( (author_name == 'all' and tagg == 'all' and p_tagg=='all') ):
                    if sci_scopus!=0:
                        result[key] = publication
                    else:
                        return render_template('search.html', publications=publications,l=len(publications))
                elif author_name=='all' and tagg == 'all':
                    if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                        result[key] = publication

                elif author_name == 'all' and p_tagg == 'all':
                    for author_key, author in publication.get('authors').items():
                        if author.get('tagg') == tagg:
                            result[key]=publication
                            
                elif tagg == 'all' and p_tagg == 'all':
                    for author_key, author in publication.get('authors').items():
                        temp=author.get('name').strip()
                        if author_name in temp.lower():
                            result[key]=publication
                            
                elif author_name == 'all':
                    if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                        for author_key, author in publication.get('authors').items():
                            if author.get('tagg') == tagg:
                                result[key] = publication
                                
                elif tagg == 'all':
                    if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                        for author_key, author in publication.get('authors').items():
                            temp = author.get('name').strip()
                            if author_name in temp.lower():
                                result[key] = publication

                
                elif p_tagg == 'all':
                    if str(year) == str(publication.get('year')):
                        for author_key, author in publication.get('authors').items():
                            temp = author.get('name').strip()
                            if author_name in temp.lower() and author.get('tagg') == tagg:
                                result[key] = publication
                        
                            
            elif str(year) == str(publication.get('year')):
                if( (author_name == 'all' and tagg == 'all') ):
                    result[key]=publication
                
                elif author_name == 'all' and tagg == 'all':
                    if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                        result[key] = publication
                        
                elif author_name == 'all' and p_tagg == 'all':
                    for author_key, author in publication.get('authors').items():
                        if author.get('tagg') == tagg:
                            result[key]=publication
                        

                elif tagg == 'all' and p_tagg == 'all':
                    for author_key, author in publication.get('authors').items():
                        temp = author.get('name').strip()
                        if author_name in temp.lower():
                            result[key] = publication
                        

                elif author_name == 'all':
                    if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                        for author_key, author in publication.get('authors').items():
                            if author.get('tagg') == tagg:
                                result[key] = publication
                                
                elif tagg == 'all':
                    if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                        for author_key, author in publication.get('authors').items():
                            temp = author.get('name').strip()
                            if author_name in temp.lower():
                                result[key] = publication
                            
                
                elif p_tagg == 'all':
                    for author_key, author in publication.get('authors').items():
                        temp = author.get('name').strip()
                        if author_name in temp.lower() and author.get('tagg') == tagg:
                            result[key] = publication
                            
                        
                else:
                    for author_key, author in publication.get('authors').items():
                        temp = author.get('name').strip()
                        if author_name in temp.lower() and author.get('tagg') == tagg:
                            if publication.get('publication') and publication['publication'].get('p_tagg') == p_tagg:
                                result[key] = publication
                        
        return  render_template('search.html', publications=result,l=len(result))
                        
    return render_template('search.html',publications={},l=0)





@app.route('/export')
def export():
    publications_json = request.args.get('publications')
    publications_json = publications_json.replace("'", "\"") 
    publications_json = publications_json.replace('\\', '\\\\')
    print(publications_json)
    try:
        publications = json.loads(publications_json)
    except json.decoder.JSONDecodeError:
        return "Error: Invalid JSON input"

    file_content = []

    for index, publication in enumerate(publications.values()):
        title = publication['title']
        authors = ", ".join([author['name'] for author in publication['authors'].values()])
        publication_name = publication['publication'].get('publication', 'untagged')
        year = publication['year']
        file_content.append([title, authors, publication_name, year])

    output = StringIO()
    writer = csv.writer(output)
    header = ['Title', 'Authors', 'Publication', 'Year']
    writer.writerow(header)
    writer.writerows(file_content)

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=publications.csv"
    response.headers["Content-Type"] = "text/csv"

    return response
   

@app.route('/search/untagged',methods=['GET' , 'POST'])
def untagged():
    publications_ref = database.child('Publications')
    publications = publications_ref.get()
    
    if request.method == 'POST':
        author=request.form.get('author')
        year=request.form.get('year')
        tagg=request.form.get('tagg')
        title=request.form.get('title')
        p_tagg=request.form.get('p_tagg')
        delete=request.form.get('delete')
        
        title=re.sub(r'\W+', '', title).replace(' ', '_')
        key=title+str(year)


        SCI = request.form.get("SCI")
        if SCI:
            database.child("Publications").child(key).update({"SCI": 1})
       
            
        Scopus = request.form.get("Scopus")
        if Scopus:
            database.child("Publications").child(key).update({"Scopus": 1})
        



        if tagg:
            database.child("Publications").child(key).child("authors").child(author).update({'tagg':tagg})

            authors = database.child("Publications").child(key).child("authors").get()

            all_tagged = True
            for author_key, author_data in authors.items():
                if author_data.get("tagg") == "untagged":
                    all_tagged = False
                    break

            if all_tagged:
                database.child("Publications").child(key).update({"tagg":"tagged"})

        if p_tagg:
            database.child("Publications").child(key).child("publication").update({'p_tagg':p_tagg})
        if delete:
            print("delete")
            database.child('Publications').child(key).delete()
        publications = publications_ref.get()
    # Render the HTML page with the publication data
    result = {}

    publications = publications_ref.order_by_child("tagg").equal_to("untagged").get()

    for n, publication in publications.items():
        result[n] = publication
        
    return render_template('untagged.html', publications=result)

    
 
    
    #return render_template('untagged.html', publications=publications)

@app.route('/search/tagged',methods=['GET' , 'POST'])
def tagged():
    publications_ref = database.child('Publications')
    publications = publications_ref.get()
    
    if request.method == 'POST':
        author=request.form.get('author')
        year=request.form.get('year')
        tagg=request.form.get('tagg')
        title=request.form.get('title')
        p_tagg=request.form.get('p_tagg')
        delete=request.form.get('delete')

        title=re.sub(r'\W+', '', title).replace(' ', '_')
        key=title+str(year)

        SCI = request.form.get("SCI")
        if SCI:
            database.child("Publications").child(key).update({"SCI": 1})
        else:
            database.child("Publications").child(key).update({"SCI": 0})
            
        Scopus = request.form.get("Scopus")
        if Scopus:
            database.child("Publications").child(key).update({"Scopus": 1})
        else:
            database.child("Publications").child(key).update({"Scopus": 0})


        if tagg:
            database.child("Publications").child(key).child("authors").child(author).update({'tagg':tagg})
        if p_tagg:
            database.child("Publications").child(key).child("publication").update({'p_tagg':p_tagg})
        if delete:
            print("delete")
            database.child('Publications').child(key).delete()
        publications = publications_ref.get()
        
        
    result = {}

    publications = publications_ref.order_by_child("tagg").equal_to("tagged").get()

    for n, publication in publications.items():
        result[n] = publication
        
    return render_template('tagged.html', publications=result)



    



