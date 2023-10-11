import os
import requests
import shutil
import subprocess
from subprocess import CREATE_NEW_CONSOLE
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk

supported_flavors = ["spigot", "paper"]
supported_flavors_str = ", ".join(supported_flavors)


def copy_template_to_folder(path_to_folder):
    # Copy the contents of the "template" folder to the newly created folder
    template_folder = "template"
    if os.path.exists(template_folder):
        for item in os.listdir(template_folder):
            source_item = os.path.join(template_folder, item)
            destination_item = os.path.join(path_to_folder, item)
            if os.path.isdir(source_item):
                shutil.copytree(source_item, destination_item)
            else:
                shutil.copy2(source_item, destination_item)
        print(f"Template contents copied to '{path_to_folder}'.")
    else:
        print(f"Template folder '{template_folder}' does not exist.")


def find_supported_flavor_folders():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    supported_folders = []

    # List all items (files and folders) in the script's directory
    items = os.listdir(script_directory)

    # Iterate through the items and check for folders with flavors in the supported_flavors list
    for item in items:
        item_path = os.path.join(script_directory, item)
        if os.path.isdir(item_path):
            for flavor in supported_flavors:
                if item.startswith(f"{flavor}-"):
                    supported_folders.append(item)
                    break  # No need to check other flavors once matched

    return supported_folders


def execute_start_script(folder_name):
    # Create the path to the "start.bat" script
    start_script_path = os.path.join(folder_name, "start.bat")

    # Check if the "start.bat" file exists in the specified folder
    if os.path.exists(start_script_path):
        try:
            # Execute the "start.bat" script in a new command prompt window
            subprocess.Popen(["cmd", "/c", start_script_path], cwd=folder_name)
            print(f"Started the server in folder: {folder_name}")
        except Exception as e:
            print(f"An error occurred while executing the start script: {e}")
    else:
        print(f"The 'start.bat' script does not exist in folder: {folder_name}")


# https://cdn.getbukkit.org/spigot/spigot-1.10.2-R0.1-SNAPSHOT-latest.jar
# https://download.getbukkit.org/spigot/spigot-1.20.2.jar
def download_spigot(spigot_version):
    first_attempt_url = f"https://download.getbukkit.org/spigot/spigot-{spigot_version}.jar"
    second_attempt_url = f"https://cdn.getbukkit.org/spigot/spigot-{spigot_version}.jar"
    third_attempt_url = f"https://download.getbukkit.org/spigot/spigot-{spigot_version}-R0.1-SNAPSHOT-latest.jar"
    fourth_attempt_url = f"https://cdn.getbukkit.org/spigot/spigot-{spigot_version}-R0.1-SNAPSHOT-latest.jar"

    # Define the content of the <title> tag that indicates failure
    restricted_title = "GetBukkit CDN - Restricted"

    # First attempt
    first_attempt = download_jar(first_attempt_url)
    if first_attempt is not None and not check_restricted_title(first_attempt_url):
        return first_attempt

    # Second attempt: get from cdn
    second_attempt = download_jar(second_attempt_url)
    if second_attempt is not None and not check_restricted_title(second_attempt_url):
        return second_attempt

    # Third attempt: append -R0.1-SNAPSHOT-latest
    third_attempt = download_jar(third_attempt_url)
    if third_attempt is not None and not check_restricted_title(third_attempt_url):
        return third_attempt

    # Final attempt: get from cdn and append -R0.1-SNAPSHOT-latest
    fourth_attempt = download_jar(fourth_attempt_url)
    if fourth_attempt is not None and not check_restricted_title(fourth_attempt_url):
        return fourth_attempt

    # If all attempts fail, return None
    return None


def download_paper(paper_version):
    return download_jar(get_latest_paper_build(paper_version))


def get_latest_paper_build(paper_version):
    builds_url = f"https://api.papermc.io/v2/projects/paper/versions/{paper_version}/builds"
    builds_response = requests.get(builds_url)
    builds_data = builds_response.json()

    # Check if the response was successful
    if builds_response.status_code == 200:
        builds = builds_data["builds"]
        if builds:
            # Find the build with the highest build number
            highest_build = max(builds, key=lambda x: x["build"])

            # Extract build number and downloads.application.name
            build_number = highest_build["build"]
            application_name = highest_build["downloads"]["application"]["name"]

            return f"https://api.papermc.io/v2/projects/paper/versions/{paper_version}/builds/{build_number}/downloads/{application_name}"
        else:
            print("No builds found for the specified version.")
            return None
    else:
        print(f"Failed to query builds. Status code: {builds_response.status_code}")
        return None


def download_jar(jar_url):
    try:
        jar_download_response = requests.get(jar_url)
        if jar_download_response.status_code == 200:
            return jar_download_response.content
        else:
            print(f"Failed to download JAR file. Status code: {jar_download_response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def check_restricted_title(url):
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the <title> element
            title_element = soup.find("title")

            if title_element is not None:
                title_content = title_element.get_text()
                return "GetBukkit CDN - Restricted" in title_content
            else:
                return False  # No <title> element found

        else:
            return False  # HTTP request failed

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False  # Error occurred


def get_spigot_versions():
    # Define the URL
    url = "https://getbukkit.org/download/spigot"

    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all the <h2> elements
            h2_elements = soup.find_all("h2")

            # Extract the text inside the <h2> elements and store them in a list
            versions_list = [element.get_text() for element in h2_elements]

            return versions_list
        else:
            print(f"Failed to fetch spigot-version data. Status code: {response.status_code}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []


def get_paper_versions():
    # Define the URL
    url = "https://api.papermc.io/v2/projects/paper"

    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Extract the "versions" list
            versions_list = data.get("versions", [])

            return versions_list
        else:
            print(f"Failed to fetch paper-version data. Status code: {response.status_code}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []


# Create variables of cached versions available for each flavor
cached_spigot_versions = get_spigot_versions()
cached_paper_versions = get_paper_versions()


def create_server(minecraft_version, flavor):
    # Validate spigot-flavor
    if not flavor.lower() in supported_flavors:
        print(f"Unable to find a spigot-flavor named {flavor}")
        exit()

    server_folder = f"{flavor}-{minecraft_version}"
    server_folder_full_path = os.path.abspath(server_folder)

    # Create server folder or run server
    if not os.path.exists(server_folder):
        # Create a new folder based on the provided version
        os.mkdir(server_folder)
    else:
        # If the server folder already exists, run the start.bat file (if it exists)
        start_script = os.path.join(server_folder_full_path, "start.bat")
        if os.path.exists(start_script):
            print(f"Server already exists for '{server_folder}', running now.")
            subprocess.Popen([start_script], cwd=server_folder_full_path, shell=True)
            exit()
        else:
            print(f"Start script doesn't exist in {server_folder}, unable to start automatically...")
            exit()

    # Get the desired spigot flavor
    match flavor:
        case "spigot":
            server_jar = download_spigot(minecraft_version)
        case "paper":
            server_jar = download_paper(minecraft_version)
        case _:
            print(f"Unable to find a spigot-flavor named {flavor}")
            exit()

    # Define the path where you want to save the downloaded file
    output_file_path = os.path.join(server_folder, f"server.jar")
    # Save server jar
    with open(output_file_path, "wb") as output_file:
        output_file.write(server_jar)
    print(f"File downloaded successfully as '{output_file_path}'.")

    # Copy the contents of the "template" folder to the newly created folder
    copy_template_to_folder(server_folder)

    print(f"Server created successfully, running now")
    start_script = os.path.join(server_folder_full_path, "start.bat")
    if os.path.exists(start_script):
        subprocess.Popen([start_script], cwd=server_folder_full_path, shell=True)


def create_gui():
    # Create a GUI window
    root = tk.Tk()
    root.title("Minecraft Server Creator")

    # Set the size of the GUI window (width x height)
    root.geometry("600x400")  # Adjust the dimensions as needed

    # Add a label and combobox for Spigot flavor selection
    flavor_label = tk.Label(root, text="Select Spigot Flavor:")
    flavor_label.pack()
    flavor_combobox = ttk.Combobox(root, values=supported_flavors)
    flavor_combobox.pack()

    # Add a label and combobox for Minecraft version selection
    version_label = tk.Label(root, text="Select Minecraft Version:")
    version_label.pack()
    version_combobox = ttk.Combobox(root, values=[])  # Empty for now

    def on_flavor_selected(event):
        selected_flavor = flavor_combobox.get()
        if selected_flavor == "spigot":
            version_combobox["values"] = cached_spigot_versions
        elif selected_flavor == "paper":
            version_combobox["values"] = cached_paper_versions
        else:
            version_combobox["values"] = []  # No values for other flavors

    flavor_combobox.bind("<<ComboboxSelected>>", on_flavor_selected)
    version_combobox.pack()

    # Create a function for creating a server from the gui
    def on_create_server():
        minecraft_version = version_combobox.get()
        flavor = flavor_combobox.get()
        create_server(minecraft_version, flavor)

    # Create a button to create the server
    create_button = tk.Button(root, text="Create Server", command=on_create_server)
    create_button.pack()

    # Create buttons for each flavor folder
    for folder in find_supported_flavor_folders():
        def start_server(server_folder=folder):
            server_folder_full_path = os.path.abspath(server_folder)
            start_script = os.path.join(server_folder_full_path, "start.bat")

            if not os.path.exists(start_script):
                print(f"Start script doesn't exist for {server_folder}, creating one...")
                # Create the start.bat file with the specified content
                with open(start_script, "w") as start_script_file:
                    start_script_file.write("@echo off\n")
                    start_script_file.write(f"start /B cmd /k java -Xms2G -Xmx2G -XX:+UseG1GC -DIReallyKnowWhatIAmDoingISwear -jar server.jar --nogui\n")
                    start_script_file.write("pause")

            # Run the start.bat file
            execute_start_script(server_folder_full_path)

        button = tk.Button(root, text=f"Start {folder}", command=start_server)
        button.pack()

    # Add a label to display the result
    result_label = tk.Label(root, text="")
    result_label.pack()

    root.mainloop()


def main():
    # Prompt the user if they want to use gui mode
    create_gui()
    # if input("Do you want to use the built-in gui? Y/N ").lower() == "y":
    #     create_gui()
    # else:
    #     # Prompt the user for the Minecraft version
    #     minecraft_version = input("Enter the Minecraft version (e.g., 1.19.1, 1.20, 1.20.2, etc.): ")
    #     server_jar_type = input(f"Enter the Server Type [{supported_flavors_str}]: ").lower()
    #
    #     create_server(minecraft_version, server_jar_type)


if __name__ == "__main__":
    main()
