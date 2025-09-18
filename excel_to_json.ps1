param(
    [Parameter(Mandatory=$true)]
    [string]$ExcelFilePath
)

# Check if the file exists
if (-not (Test-Path $ExcelFilePath)) {
    Write-Error "File not found: $ExcelFilePath"
    exit 1
}

try {
    # Create Excel COM object
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    
    # Open the workbook
    $workbook = $excel.Workbooks.Open($ExcelFilePath)
    $worksheet = $workbook.Worksheets.Item(1)
    
    # Get the used range
    $usedRange = $worksheet.UsedRange
    $rowCount = $usedRange.Rows.Count
    $colCount = $usedRange.Columns.Count
    
    # Get headers from first row
    $headers = @()
    for ($col = 1; $col -le $colCount; $col++) {
        $headerValue = $worksheet.Cells.Item(1, $col).Value2
        if ($headerValue -eq $null) { $headerValue = "Column$col" }
        $headers += $headerValue
    }
    
    # Create array to hold data
    $data = @()
    
    # Process each row (starting from row 2)
    for ($row = 2; $row -le $rowCount; $row++) {
        $rowData = @{}
        for ($col = 1; $col -le $colCount; $col++) {
            $cellValue = $worksheet.Cells.Item($row, $col).Value2
            $rowData[$headers[$col-1]] = $cellValue
        }
        $data += $rowData
    }
    
    # Convert to JSON and output
    $jsonOutput = $data | ConvertTo-Json -Depth 10
    Write-Output $jsonOutput
    
} catch {
    Write-Error "Error processing Excel file: $($_.Exception.Message)"
} finally {
    # Clean up
    if ($workbook) { $workbook.Close($false) }
    if ($excel) { 
        $excel.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    }
}
