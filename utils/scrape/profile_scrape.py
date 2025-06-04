from bs4 import BeautifulSoup


def extract_profile(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")

    div_element = soup.find("div", attrs={"class": "content"})

    response = {}
    try:
        if div_element:
            print("successfully get the div_element")
            p_element = div_element.find("p")
            if p_element:
                response["name"] = p_element.get_text().strip()
                print("successfully get the p_element")

            register_number_element = div_element.find("label", attrs={"for": "no"})
            if register_number_element:
                print("successfully find register_number")
                response["registration_number"] = (
                    register_number_element.get_text().strip()
                )
            else:
                print("does  not get register_number_element")

            branch_name_element = div_element.find("label", attrs={"for": "branchno"})
            if branch_name_element:
                response["branch_name"] = branch_name_element.get_text().strip()
            else:
                print("does not get branch_name_element")

            return response

        return None
    except Exception as e:
        print(f"some error in scraping profile, {str(e)}")


if __name__ == "__main__":
    file_location = (
        "/home/ujjawal/personal_project/vtop_production/html_content/profile.html"
    )
    with open(file_location, "r") as f:
        html_content = f.read()

    response = extract_profile(html_content)

    if response:
        print(response)
    else:
        print("some error in scraping")
