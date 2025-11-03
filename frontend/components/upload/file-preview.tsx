"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { ChevronDown, ChevronUp, FileSpreadsheet } from "lucide-react"

interface FilePreviewProps {
  readonly file: File | null
  readonly maxRows?: number
}

export function FilePreview({ file, maxRows = 10 }: FilePreviewProps) {
  const [data, setData] = useState<any[]>([])
  const [headers, setHeaders] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    if (!file) {
      setData([])
      setHeaders([])
      return
    }

    async function parseFile() {
      if (!file) return
      
      setLoading(true)
      setError(null)

      try {
        const fileExtension = file.name.split('.').pop()?.toLowerCase()

        if (fileExtension === 'csv') {
          const text = await file.text()
          const lines = text.split('\n').filter(line => line.trim())
          
          if (lines.length === 0) {
            setError("File is empty")
            return
          }

          // Parse CSV (simple comma-separated, handle quoted values)
          const parseCSVLine = (line: string): string[] => {
            const result: string[] = []
            let current = ''
            let inQuotes = false

            for (let i = 0; i < line.length; i++) {
              const char = line[i]
              if (char === '"') {
                inQuotes = !inQuotes
              } else if (char === ',' && !inQuotes) {
                result.push(current.trim())
                current = ''
              } else {
                current += char
              }
            }
            result.push(current.trim())
            return result
          }

          const parsedHeaders = parseCSVLine(lines[0])
          setHeaders(parsedHeaders)

          const rows = lines.slice(1).map(line => {
            const values = parseCSVLine(line)
            const row: any = {}
            parsedHeaders.forEach((header, idx) => {
              row[header] = values[idx] || ''
            })
            return row
          })

          setData(rows)
        } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
          if (!file) return
          
          // Dynamically import xlsx to avoid SSR issues
          const XLSX = await import('xlsx')
          const arrayBuffer = await file.arrayBuffer()
          const workbook = XLSX.read(arrayBuffer, { type: 'array' })
          const firstSheetName = workbook.SheetNames[0]
          const worksheet = workbook.Sheets[firstSheetName]
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' })

          if (jsonData.length === 0) {
            setError("File is empty")
            return
          }

          const parsedHeaders = (jsonData[0] as any[]).map((h: any) => String(h || ''))
          setHeaders(parsedHeaders)

          const rows = (jsonData.slice(1) as any[][]).map((row: any[]) => {
            const obj: any = {}
            parsedHeaders.forEach((header, idx) => {
              obj[header] = row[idx] !== undefined ? String(row[idx]) : ''
            })
            return obj
          })

          setData(rows)
        } else {
          setError("Unsupported file format. Please upload CSV or Excel file.")
        }
      } catch (err: any) {
        setError(err.message || "Failed to parse file")
        console.error("File parsing error:", err)
      } finally {
        setLoading(false)
      }
    }

    parseFile()
  }, [file])

  if (!file) {
    return null
  }

  if (loading) {
    return (
      <Card className="border-border/50 ">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            File Preview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[200px] text-muted-foreground">
            Loading preview...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            File Preview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-destructive text-sm py-4">{error}</div>
        </CardContent>
      </Card>
    )
  }

  const displayRows = showAll ? data : data.slice(0, maxRows)
  const hasMore = data.length > maxRows

  return (
    <Card className="border-border/50 max-w-full overflow-hidden">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSpreadsheet className="h-5 w-5" />
          File Preview
          <span className="text-sm font-normal text-muted-foreground ml-2">
            ({data.length} row{data.length !== 1 ? 's' : ''})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        <div className="overflow-x-auto rounded-md border border-border max-w-full -mx-2">
          <Table className="max-w-full">
            <TableHeader>
              <TableRow>
                {headers.map((header, idx) => (
                  <TableHead key={`header-${idx}-${header}`} className="font-semibold text-xs">
                    {header || `Column ${idx + 1}`}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {displayRows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={headers.length} className="text-center text-muted-foreground py-8">
                    No data rows found
                  </TableCell>
                </TableRow>
              ) : (
                displayRows.map((row, rowIdx) => (
                  <TableRow key={`row-${rowIdx}`}>
                    {headers.map((header, colIdx) => (
                      <TableCell key={`cell-${rowIdx}-${colIdx}-${header}`} className="text-xs max-w-[200px] truncate">
                        {row[header] !== undefined && row[header] !== null ? String(row[header]) : ''}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        
        {hasMore && (
          <div className="mt-4 flex justify-center px-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAll(!showAll)}
              className="gap-2"
            >
              {showAll ? (
                <>
                  <ChevronUp className="h-4 w-4" />
                  Show Less
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" />
                  Show All {data.length} Rows
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

