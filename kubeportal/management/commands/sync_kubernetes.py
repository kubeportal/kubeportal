from django.core.management.base import BaseCommand
from colorama import init, Fore, Style

from kubeportal.kubernetes import sync


class Command(BaseCommand):
    ''' Synchronize database with Kubernetes API server. '''

    def print_line(self, log_entry):
        if log_entry['severity'] == 'error':
            print(Fore.RED + log_entry['msg'])
            print(Style.RESET_ALL, end='')
        elif log_entry['severity'] == 'warning':
            print(Fore.YELLOW + log_entry['msg'])
            print(Style.RESET_ALL, end='')
        else:
            print(log_entry['msg'])

    def handle(self, *args, **option):
        init()

        ns_logs, svca_logs = sync()
        print("Namespace synchronization:")
        for line in ns_logs:
            self.print_line(line)
        print("\nService account synchronization:")
        for line in svca_logs:
            self.print_line(line)
