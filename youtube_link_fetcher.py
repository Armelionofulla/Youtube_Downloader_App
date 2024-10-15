import csv
import time
from tkinter import messagebox

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def open_youtube_and_fetch_links(url, driver_path, output_file='links_and_titles.csv'):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(5)  # Allow page to load fully

        # Initial scrolling setup
        last_height = driver.execute_script("return document.documentElement.scrollHeight")

        # Continue scrolling until no new content loads
        while True:
            # Scroll down to the bottom
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(3)  # Wait for new content to load

            # Check if the page height has increased
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break  # Exit loop if no new content
            last_height = new_height

        # Use JavaScript to collect video links and titles directly from the DOM
        fetch_links_titles_js = """
        let videoData = [];
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            if (link.id === "video-title" && link.href) {
                let videoUrl = link.href.split('&list=')[0];  // Save only unique video URLs
                let videoTitle = link.textContent.trim();      // Get the video title
                videoData.push({url: videoUrl, title: videoTitle});
            }
        });
        return videoData;
        """

        # Execute the script to fetch video URLs and titles
        array_videos = driver.execute_script(fetch_links_titles_js)

        # Save the video URLs and titles to a CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            # writer.writerow(["Title", "URL"])  # Write the header row
            for video_data in array_videos:
                writer.writerow([video_data['title'], video_data['url']])  # Save title and URL

        # Close the browser
        driver.close()
        driver.quit()

        # Display success message
        messagebox.showinfo("Success", f"Links and titles successfully saved!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        print(f"Error fetching YouTube links and titles: {e}")

    finally:
        # Ensure the browser is closed in case of any exception
        try:
            driver.quit()
        except:
            pass  # In case driver is already closed

    return output_file  # Return the CSV file name

