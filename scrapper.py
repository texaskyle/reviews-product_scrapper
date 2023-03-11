# import the necessary requirement
from flask import Flask, request, render_template, jsonify
import pymongo
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import requests

#initilizing the flask app with the name app
app = Flask(__name__)


@app.route('/', methods=['GET'])
def homepage():
    return render_template("index.html")


@app.route('/scrap', methods=['POST'])  # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        # obtaining the search string obtained in the form
        searchString = request.form['content'].replace(" ", "")

        # checking if there was an ealier search which stored the results inside the database
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017")
            # connecting to the database called dbCrawler and if it doesnt exist it will be created
            db = dbConn['dbCrawler']
            # searching the colection same as searchString and finding out whether there is any data inside
            reviews = db[searchString].find({})

            # if there is a collection with the same name as the searchString then and it contain data then the result will be rendered to index.html
            if len(list(reviews)) > 0:
                return render_template('result.html', reviews=reviews)
            else:
                jumia_url = "https://www.jumia.co.ke/catalog/?q=" + searchString # this url is to search for the product on jumia
                response = uReq(jumia_url)  #requsting the webpage from the internet
                jumia_page = response.read()  # reading the url
                response.close()  # closing the connection from the webserver

                # debugging statement
                print(f"jumia_page: {jumia_page}")

                jumia_html = bs(jumia_page, 'html.parser')  # parsing the webpage as html
                # find the appropriate tag to redirect to the product page
                bigboxes = jumia_html.findAll("div", {"class":"prd _fb _spn c-prd col"})

                if len(bigboxes) == 0:
                    return "no result for {}".format(searchString)
                box = bigboxes[0]
                product_link = "https://www.jumia.co.ke" + box.a['href'] # extracting the actual product
                prodReq = requests.get(product_link) # getting the product from the server

                # debugging statement
                print(f"prodReq status code: {prodReq.status_code}")

                prod_html = bs(prodReq.text, 'html.parser')  # parsing the product as html
                commentBoxes = prod_html.find_all("div", {'class': '-pvs -hr _bet'})  # finding in the html the section that contains the customers comment

                # creating a collection with tha same name as the search string
                table = db[searchString]
                reviews = []  # initializing an empty list for the reviews
                for commentbox in commentBoxes:
                    try:
                        name = commentbox.div.div.span[1]
                    except:
                        name = 'no name'
                    try:
                        rating = commentbox.div.text
                    except:
                        rating  = 'no rating'
                    try:
                        comment_tag = commentbox.p.text
                    except:
                        comment_tag = "no comment"

                    # saving the details to the dictionary
                    my_dict = {"product": searchString,
                               "name": name,
                               "rating": rating,
                               "comment_tag": comment_tag}
                    # inserting my_dict into the dictionary
                    x = table.insert_one(my_dict)
                    # appending my_dict into the review list
                    reviews.append(my_dict)
        except:
            return "Something went wrong"
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(port=8000, debug=True)
