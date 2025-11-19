import subprocess
import tempfile
import os
import sys

def pypwsh_dropdown(options_list=["","Rose","Tulip"], allowBlankSubmission=True, removeBlankEntriesFromList=False, allowEditingListItems=True):
    ps_template = r"""
$allowBlankSubmission = $PLACE_HOLDER_allowBlankSubmission
$removeBlankEntriesFromList = $PLACE_HOLDER_removeBlankEntriesFromList
$allowEditingListItems = $PLACE_HOLDER_allowEditingListItems

$xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Editable List Chooser" Width="400" Height="300" ResizeMode="NoResize" WindowStartupLocation="CenterScreen">
    <StackPanel Margin="20">
        <Label Content="1. Select a list entry to edit or confirm:" FontSize="14"/>
        <ComboBox x:Name="OptionsComboBox" Margin="0,5,0,10"/>
        
        <Label Content="2. Edit the selection (optional):" FontSize="12"/>
        <TextBox x:Name="EditTextBox" Margin="0,5,0,5"/>
        <Button x:Name="ApplyButton" Content="Apply Edit" Padding="5" Margin="0,0,0,10"/>

        <StackPanel Orientation="Horizontal" HorizontalAlignment="Center">
            <Button x:Name="ConfirmButton" Content="Confirm Choice" Padding="10,5" Margin="0,0,10,0" Width="120"/>
            <Button x:Name="ResetButton" Content="Reset List" Padding="10,5" Width="120"/>
        </StackPanel>
    </StackPanel>
</Window>
"@

$InitialList = $PLACE_HOLDER_InitialList

if ($removeBlankEntriesFromList) {
    $FilteredList = $InitialList | Where-Object { $_ -ne "" }
} else {
    $FilteredList = $InitialList
}

$OptionList = New-Object System.Collections.ArrayList
$OptionList.AddRange($FilteredList)

Add-Type -A PresentationFramework, WindowsBase, System.Xaml

[xml]$x = $xaml
$xReader = (New-Object System.Xml.XmlNodeReader $x)
$w = [Windows.Markup.XamlReader]::Load($xReader)

$ComboBox = $w.FindName("OptionsComboBox")
$EditTextBox = $w.FindName("EditTextBox")
$ApplyButton = $w.FindName("ApplyButton")
$ConfirmButton = $w.FindName("ConfirmButton")
$ResetButton = $w.FindName("ResetButton")

function Check-ApplyButtonState {
    if (-not $allowEditingListItems) { 
        return 
    }

    $selectedIndex = $ComboBox.SelectedIndex
    if ($selectedIndex -ge 0) {
        $selectedItem = $OptionList[$selectedIndex]
        $currentText = $EditTextBox.Text

        $isDifferent = $currentText -ne $selectedItem
        $isValidText = $allowBlankSubmission -or ($currentText -ne "")

        $ApplyButton.IsEnabled = $isDifferent -and $isValidText
    } else {
        $ApplyButton.IsEnabled = $false
    }
}

function Update-ComboBox {
    [void]$ComboBox.Items.Clear()
    foreach ($item in $OptionList) {
        [void]$ComboBox.Items.Add($item)
    }
    [void]($ComboBox.SelectedIndex = 0)
    
    if (-not $allowEditingListItems) {
        $EditTextBox.IsEnabled = $false
        $ApplyButton.IsEnabled = $false
    } else {
        $EditTextBox.IsEnabled = $true
        $ApplyButton.IsEnabled = $true 
    }
}

$ComboBox.Add_SelectionChanged({
    $selectedIndex = $ComboBox.SelectedIndex
    if ($selectedIndex -ge 0) {
        $itemValue = $OptionList[$selectedIndex]
        
        $EditTextBox.Text = $itemValue 
        
        if ($allowEditingListItems) {
            $EditTextBox.IsEnabled = $true
        }
        
        Check-ApplyButtonState 
    }
})

$ApplyButton.Add_Click({
    if (-not $allowEditingListItems) { 
        return 
    }

    $selectedIndex = $ComboBox.SelectedIndex
    if ($selectedIndex -ge 0) {
        $OptionList[$selectedIndex] = $EditTextBox.Text
        
        Update-ComboBox
        
        [void]($ComboBox.SelectedIndex = $selectedIndex)
        
        Check-ApplyButtonState 
    }
})

$ResetButton.Add_Click({
    $OptionList.Clear()
    
    if ($removeBlankEntriesFromList) {
        $ResetFilteredList = $InitialList | Where-Object { $_ -ne "" }
    } else {
        $ResetFilteredList = $InitialList
    }
    
    $OptionList.AddRange($ResetFilteredList)
    Update-ComboBox
    Check-ApplyButtonState 
    [System.Windows.MessageBox]::Show("List restored to original entries.", "Reset Complete")
})

$ConfirmButton.Add_Click({
    $ChosenOption = $OptionList[$ComboBox.SelectedIndex]
    
    if ($ChosenOption -eq "" -and $allowBlankSubmission -eq $false) {
        [System.Windows.MessageBox]::Show("Submission failed: Blank entries are not allowed.", "Error", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Warning)
    } else {
        [Console]::WriteLine($ChosenOption) 
        $w.Close()
    }
})

$EditTextBox.Add_TextChanged({
    if (-not $allowEditingListItems) { return }
    Check-ApplyButtonState
})

Update-ComboBox

$EditTextBox.Text = $OptionList[$ComboBox.SelectedIndex] 

Check-ApplyButtonState 

$w.ShowDialog() | Out-Null
"""

    ps_list_items = ', '.join(f'"{item}"' for item in options_list)
    ps_initial_list = f'@({ps_list_items})'
    
    ps_allow_editing = f"${str(allowEditingListItems).lower()}"
    ps_allow_blank = f"${str(allowBlankSubmission).lower()}"
    ps_remove_blank = f"${str(removeBlankEntriesFromList).lower()}"
    
    script_content = ps_template.replace(
        "$PLACE_HOLDER_allowBlankSubmission", ps_allow_blank
    ).replace(
        "$PLACE_HOLDER_removeBlankEntriesFromList", ps_remove_blank
    ).replace(
        "$PLACE_HOLDER_allowEditingListItems", ps_allow_editing 
    ).replace(
        "$PLACE_HOLDER_InitialList", ps_initial_list
    )
    
    tmp_path = ""
    captured_output = ""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(script_content)
            tmp_path = tmp_file.name
        
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", tmp_path],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8' 
        )

        captured_output = result.stdout.rstrip()
        
    except subprocess.CalledProcessError as e:
        return ""

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    # Filter for the actual choice, which is the last non-empty line printed to stdout via [Console]::WriteLine
    final_choice = [line for line in captured_output.splitlines() if line][-1] if captured_output else ""
    return final_choice

def pypwsh_filebrowse(initial_path="", filter="All Files (*.*)|*.*", title="Select a File"):
    ps_template = r"""
param(
    [string]$InitialPath,
    [string]$Filter,
    [string]$Title
)

# 1. Load the necessary WPF assemblies and required WinForms assembly for OpenFileDialog
Add-Type -AssemblyName PresentationFramework, WindowsBase, System.Xaml, System.Windows.Forms

# 2. XAML UI definition (Embedded)
$xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="File Path Browser"
    Width="500" Height="250"
    ResizeMode="NoResize">
    <StackPanel Margin="15">
        <Label Content="Selected File Path:" Margin="0,0,0,5"/>
        <TextBox
            x:Name="PathTextBox"
            Height="60"
            TextWrapping="Wrap"
            AcceptsReturn="True"
            VerticalScrollBarVisibility="Auto"
            Margin="0,0,0,15" />
        <Grid>
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="100"/>
            </Grid.ColumnDefinitions>
            <Button 
                x:Name="BrowseButton" Content="Browse File" Grid.Column="0" Margin="0,0,10,0" Padding="5"/>
            <Button x:Name="ConfirmButton" Content="Confirm Path" Grid.Column="1" Padding="5"/>
        </Grid>
    </StackPanel>
</Window>
"@

[xml]$x = $xaml
$reader = (New-Object System.Xml.XmlNodeReader $x)
$window = [Windows.Markup.XamlReader]::Load($reader)

# 3. Get controls
$textBox = $window.FindName("PathTextBox")
$browseButton = $window.FindName("BrowseButton")
$confirmButton = $window.FindName("ConfirmButton")

# Set initial path in TextBox
$textBox.Text = $InitialPath 

# 4. Define Browse Button Action (using OpenFileDialog for files)
$browseButton.Add_Click({
    # Create the file browser object
    $fileBrowser = New-Object System.Windows.Forms.OpenFileDialog
    
    # Set filters and title from parameters
    $fileBrowser.Filter = $Filter
    $fileBrowser.Title = $Title

    # Set initial directory if the current text is a directory
    $currentText = $textBox.Text.Trim()
    if (-not [string]::IsNullOrEmpty($currentText) -and (Test-Path -Path $currentText -PathType Container)) {
        $fileBrowser.InitialDirectory = $currentText
    } elseif (-not [string]::IsNullOrEmpty($currentText) -and (Test-Path -Path $currentText -PathType Leaf)) {
        $fileBrowser.InitialDirectory = [System.IO.Path]::GetDirectoryName($currentText)
        $fileBrowser.FileName = [System.IO.Path]::GetFileName($currentText)
    }

    # Show the dialog
    $result = $fileBrowser.ShowDialog()

    # Check if the user clicked OK
    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        # Update the TextBox with the selected path
        $textBox.Text = $fileBrowser.FileName
    }
})

# 5. Define Confirm Button Action
$confirmButton.Add_Click({
    $selectedPath = $textBox.Text.Trim()
    
    if (Test-Path -Path $selectedPath -PathType Leaf) {
        [Console]::WriteLine($selectedPath) # Output the final choice for Python to capture
        $window.Close()
    } elseif ([string]::IsNullOrEmpty($selectedPath)) {
        [System.Windows.MessageBox]::Show("Please browse or enter a file path.", "Error", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Error)
    } else {
        [System.Windows.MessageBox]::Show("Error: The path is invalid or does not point to a file.", "Error", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Error)
    }
})

# 6. Display the window
$window.ShowDialog() | Out-Null
"""

    if initial_path is None:
        initial_path = ""
        
    tmp_path = ""
    captured_output = ""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(ps_template)
            tmp_path = tmp_file.name
        
        command = [
            "powershell", 
            "-ExecutionPolicy", "Bypass", 
            "-File", tmp_path, 
            "-InitialPath", initial_path,
            "-Filter", filter,
            "-Title", title
        ]
        
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8' 
        )

        captured_output = result.stdout.rstrip()
        
    except subprocess.CalledProcessError as e:
        return "" 

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    final_choice = captured_output.splitlines()[-1].strip() if captured_output else ""
    return final_choice

import subprocess
import tempfile
import os
import sys

def pypwsh_folderbrowse(initial_path="", description="Select a Folder", title="Folder Browser"):
    ps_template = r"""
param(
    [string]$InitialPath,
    [string]$Description,
    [string]$Title
)

Add-Type -AssemblyName PresentationFramework, WindowsBase, System.Xaml, System.Windows.Forms

$xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Folder Browser"
    Width="500" Height="250"
    ResizeMode="NoResize">
    <StackPanel Margin="15">
        <Label Content="Selected Folder Path:" Margin="0,0,0,5"/>
        <TextBox
            x:Name="PathTextBox"
            Height="60"
            TextWrapping="Wrap"
            AcceptsReturn="True"
            VerticalScrollBarVisibility="Auto"
            Margin="0,0,0,15" />
        <Grid>
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="100"/>
            </Grid.ColumnDefinitions>
            <Button x:Name="BrowseButton" Content="Browse Folder" Grid.Column="0" Margin="0,0,10,0" Padding="5"/>
            <Button x:Name="ConfirmButton" Content="Confirm Path" Grid.Column="1" Padding="5"/>
        </Grid>
    </StackPanel>
</Window>
"@

[xml]$x = $xaml
$reader = (New-Object System.Xml.XmlNodeReader $x)
$window = [Windows.Markup.XamlReader]::Load($reader)

$window.Title = $Title

$textBox = $window.FindName("PathTextBox")
$browseButton = $window.FindName("BrowseButton")
$confirmButton = $window.FindName("ConfirmButton")

$textBox.Text = $InitialPath 

$browseButton.Add_Click({
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = $Description
    
    $currentText = $textBox.Text.Trim()
    if (-not [string]::IsNullOrEmpty($currentText) -and (Test-Path -Path $currentText -PathType Container)) {
        $folderBrowser.SelectedPath = $currentText
    }

    $result = $folderBrowser.ShowDialog()

    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        $textBox.Text = $folderBrowser.SelectedPath
    }
})

$confirmButton.Add_Click({
    $selectedPath = $textBox.Text.Trim()
    
    if (-not [string]::IsNullOrEmpty($selectedPath) -and (Test-Path -Path $selectedPath -PathType Container)) {
        [Console]::WriteLine($selectedPath)
        $window.Close()
    } elseif ([string]::IsNullOrEmpty($selectedPath)) {
        [System.Windows.MessageBox]::Show("Please browse or enter a folder path.", "Error", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Error)
    } else {
        [System.Windows.MessageBox]::Show("Error: The path is invalid or does not point to a folder.", "Error", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Error)
    }
})

$window.ShowDialog() | Out-Null
"""

    if initial_path is None:
        initial_path = ""
        
    tmp_path = ""
    captured_output = ""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(ps_template)
            tmp_path = tmp_file.name
        
        command = [
            "powershell", 
            "-ExecutionPolicy", "Bypass", 
            "-File", tmp_path, 
            "-InitialPath", initial_path,
            "-Description", description,
            "-Title", title
        ]
        
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8' 
        )

        captured_output = result.stdout.rstrip()
        
    except subprocess.CalledProcessError as e:
        return "" 

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    final_choice = captured_output.splitlines()[-1].strip() if captured_output else ""
    return final_choice
