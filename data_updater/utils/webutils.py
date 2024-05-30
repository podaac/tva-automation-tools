'''Web utility module'''
# pylint: disable=R0903

from os import popen


class WebUtils():
    '''Class for Web related utility methods'''

    def GetUrl(url: str) -> str:
        '''Function to get the raw webpage content'''

        # Writing to file to solve timing issues with download
        output_file_name = 'temp.txt'
        command_download = f'curl -L -H "Content-Type: text/plain; charset=UTF-8" -o {output_file_name} {url}'
        print(f'Command download:\r\n{command_download}')
        popen(command_download).close()

        with open(output_file_name, 'r', encoding="utf8") as file:
            result = file.read()

        command_delete_file = f'rm {output_file_name}'
        print(f'Command read:\r\n{command_delete_file}')
        popen(command_delete_file).close()
        return result
