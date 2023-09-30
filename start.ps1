function Hide-Console
{
    $consolePtr = [Console.Window]::GetConsoleWindow()
    #0 hide
    [Console.Window]::ShowWindow($consolePtr, 0)
}



$pythonScript = "D:\Documents\python\Swiftsinc\main.PY"
Invoke-Expression "python `"$pythonScript`""

Hide-Console