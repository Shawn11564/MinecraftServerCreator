import os
import requests
import shutil
import subprocess

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


def download_spigot(spigot_version):
    return download_jar(f"https://download.getbukkit.org/spigot/spigot-{spigot_version}.jar")


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


def main():
    # Prompt the user for the Minecraft version
    minecraft_version = input("Enter the Minecraft version (e.g., 1.19.1, 1.20, 1.20.2, etc.): ")
    server_jar_type = input(f"Enter the Server Type [{supported_flavors_str}]: ").lower()

    # Validate spigot-flavor
    if not server_jar_type.lower() in supported_flavors:
        print(f"Unable to find a spigot-flavor named {server_jar_type}")
        exit()

    server_folder = f"{server_jar_type}-{minecraft_version}"
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
    match server_jar_type:
        case "spigot":
            server_jar = download_spigot(minecraft_version)
        case "paper":
            server_jar = download_paper(minecraft_version)
        case _:
            print(f"Unable to find a spigot-flavor named {server_jar_type}")
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


if __name__ == "__main__":
    main()
