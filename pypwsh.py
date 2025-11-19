# VERSION = 0.1.0

import subprocess
import tempfile
import os
import sys

def pypwsh_dropdown(options_list=["","Rose","Tulip"], allowBlankSubmission=True, removeBlankEntriesFromList=False, allowEditingListItems=True):
    # --- START OF POWERSHELL TEMPLATE ---
    ps_template = r"""
$allowBlankSubmission = $PLACE_HOLDER_allowBlankSubmission
$removeBlankEntriesFromList = $PLACE_HOLDER_removeBlankEntriesFromList
$allowEditingListItems = $PLACE_HOLDER_allowEditingListItems

Write-Host "--- INITIALIZING SCRIPT ---"

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
Write-Host "LOG: Initial list prepared. Items: $($OptionList.Count)"

Add-Type -A PresentationFramework, WindowsBase, System.Xaml

[xml]$x = $xaml
$xReader = (New-Object System.Xml.XmlNodeReader $x)
$w = [Windows.Markup.XamlReader]::Load($xReader)

$ComboBox = $w.FindName("OptionsComboBox")
$EditTextBox = $w.FindName("EditTextBox")
$ApplyButton = $w.FindName("ApplyButton")
$ConfirmButton = $w.FindName("ConfirmButton")
$ResetButton = $w.FindName("ResetButton")

# 💥 HELPER FUNCTION: To manage ApplyButton state (required for reliable UI)
function Check-ApplyButtonState {
    Write-Host "LOG: --- Check-ApplyButtonState called ---"
    if (-not $allowEditingListItems) { 
        Write-Host "LOG: Editing disallowed. Exiting."
        return 
    }

    $selectedIndex = $ComboBox.SelectedIndex
    if ($selectedIndex -ge 0) {
        $selectedItem = $OptionList[$selectedIndex]
        $currentText = $EditTextBox.Text

        $isDifferent = $currentText -ne $selectedItem
        $isValidText = $allowBlankSubmission -or ($currentText -ne "")

        $ApplyButton.IsEnabled = $isDifferent -and $isValidText
        Write-Host "LOG: Selected Item: '$selectedItem'"
        Write-Host "LOG: Current Text:  '$currentText'"
        Write-Host "LOG: Text changed (isDifferent): $isDifferent"
        Write-Host "LOG: Text is valid (isValidText): $isValidText"
        Write-Host "LOG: ApplyButton.IsEnabled set to: $($ApplyButton.IsEnabled)"
    } else {
        Write-Host "LOG: No item selected (Index: $selectedIndex). ApplyButton disabled."
        $ApplyButton.IsEnabled = $false
    }
}

function Update-ComboBox {
    Write-Host "LOG: --- Update-ComboBox called ---"
    [void]$ComboBox.Items.Clear()
    foreach ($item in $OptionList) {
        [void]$ComboBox.Items.Add($item)
    }
    [void]($ComboBox.SelectedIndex = 0)
    Write-Host "LOG: ComboBox updated and SelectedIndex set to 0."
    
    # MODIFIED: Ensure state is explicitly set on load/update
    if (-not $allowEditingListItems) {
        $EditTextBox.IsEnabled = $false
        $ApplyButton.IsEnabled = $false
        Write-Host "LOG: Editing disallowed. Controls forced disabled."
    } else {
        $EditTextBox.IsEnabled = $true
        $ApplyButton.IsEnabled = $true 
        Write-Host "LOG: Editing allowed. Controls forced enabled."
    }
}

$ComboBox.Add_SelectionChanged({
    Write-Host "LOG: *** SelectionChanged event fired ***"
    $selectedIndex = $ComboBox.SelectedIndex
    if ($selectedIndex -ge 0) {
        $itemValue = $OptionList[$selectedIndex]
        
        # Setting EditTextBox.Text here WILL trigger TextChanged event.
        $EditTextBox.Text = $itemValue 
        Write-Host "LOG: EditTextBox.Text set to: '$itemValue'"
        
        if ($allowEditingListItems) {
            $EditTextBox.IsEnabled = $true
        }
        
        Check-ApplyButtonState # For redundancy
    }
})

$ApplyButton.Add_Click({
    Write-Host "LOG: *** ApplyButton Clicked ***"
    if (-not $allowEditingListItems) { 
        Write-Host "LOG: Editing disallowed. Returning."
        return 
    }

    $selectedIndex = $ComboBox.SelectedIndex
    if ($selectedIndex -ge 0) {
        $OptionList[$selectedIndex] = $EditTextBox.Text
        Write-Host "LOG: List item at index $selectedIndex updated to: '$($EditTextBox.Text)'"
        
        Update-ComboBox
        
        [void]($ComboBox.SelectedIndex = $selectedIndex)
        
        Check-ApplyButtonState # Check state after successful apply
    }
})

$ResetButton.Add_Click({
    Write-Host "LOG: *** ResetButton Clicked ***"
    $OptionList.Clear()
    
    if ($removeBlankEntriesFromList) {
        $ResetFilteredList = $InitialList | Where-Object { $_ -ne "" }
    } else {
        $ResetFilteredList = $InitialList
    }
    
    $OptionList.AddRange($ResetFilteredList)
    Update-ComboBox
    Check-ApplyButtonState # Check state after reset
    [System.Windows.MessageBox]::Show("List restored to original entries.", "Reset Complete")
})

$ConfirmButton.Add_Click({
    Write-Host "LOG: *** ConfirmButton Clicked ***"
    $ChosenOption = $OptionList[$ComboBox.SelectedIndex]
    
    if ($ChosenOption -eq "" -and $allowBlankSubmission -eq $false) {
        Write-Host "LOG: Submission failed: Blank entry disallowed."
        [System.Windows.MessageBox]::Show("Submission failed: Blank entries are not allowed.", "Error", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Warning)
    } else {
        Write-Host "LOG: Choice confirmed: '$ChosenOption'"
        [Console]::WriteLine($ChosenOption) 
        $w.Close()
    }
})

# 💥 HANDLER: Calls helper function on TextChanged (crucial for dynamic state)
$EditTextBox.Add_TextChanged({
    Write-Host "LOG: *** EditTextBox TextChanged event fired ***"
    if (-not $allowEditingListItems) { return }
    Check-ApplyButtonState
})

# --- INITIALIZATION SEQUENCE ---
Update-ComboBox

# Ensure the EditTextBox text is set to the selected value upon load
# This triggers the TextChanged event, which calls Check-ApplyButtonState
$EditTextBox.Text = $OptionList[$ComboBox.SelectedIndex] 
Write-Host "LOG: Initial EditTextBox.Text set to: '$($EditTextBox.Text)'"

Check-ApplyButtonState # Final safety check
Write-Host "LOG: Final state check before showing dialog."

$w.ShowDialog() | Out-Null
Write-Host "--- DIALOG CLOSED ---"
"""
    # --- END OF POWERSHELL TEMPLATE ---

    ps_list_items = ', '.join(f'"{item}"' for item in options_list)
    ps_initial_list = f'@({ps_list_items})'
    
    # 💥 FIX: Ensure PowerShell sees $true or $false, not just "true" or "false"
    ps_allow_editing = f"${str(allowEditingListItems).lower()}"
    ps_allow_blank = f"${str(allowBlankSubmission).lower()}"
    ps_remove_blank = f"${str(removeBlankEntriesFromList).lower()}"
    
    script_content = ps_template.replace(
        "$PLACE_HOLDER_allowBlankSubmission", ps_allow_blank
    ).replace(
        "$PLACE_HOLDER_removeBlankEntriesFromList", ps_remove_blank
    ).replace(
        "$PLACE_HOLDER_allowEditingListItems", ps_allow_editing # This is the key fix
    ).replace(
        "$PLACE_HOLDER_InitialList", ps_initial_list
    )
    
    tmp_path = ""
    captured_output = ""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(script_content)
            tmp_path = tmp_file.name
        
        # Execute PowerShell script
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", tmp_path],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8' # Ensure consistent encoding
        )

        captured_output = result.stdout.rstrip()
        
        # LOGGING FIX: Print the full captured output to the Python console
        sys.stderr.write("\n--- POWERSHELL DEBUG LOGS ---\n")
        sys.stderr.write(result.stdout)
        sys.stderr.write("-----------------------------\n")
        
    except subprocess.CalledProcessError as e:
        sys.stderr.write("\n--- POWERSHELL ERROR LOGS ---\n")
        sys.stderr.write(f"Error Code: {e.returncode}\n")
        sys.stderr.write(e.stderr)
        sys.stderr.write("-----------------------------\n")
        return ""

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    # Return only the final choice (which is the last line printed by [Console]::WriteLine)
    final_choice = [line for line in captured_output.splitlines() if line][-1] if captured_output else ""
    return final_choice