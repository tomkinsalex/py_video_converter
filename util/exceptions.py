class ShellException(Exception):
    def __init__(self, cmd, stdout, stderr):
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr

    
    def __str__(self):
        return ' Command used: \n "%s" \n\n Standard Out: \n "%s" \n\n Standard Error: \n "%s"' % (self.cmd, self.stdout, self.stderr)