package utils

import (
	"time"
)

func FormatTimestamp(dt time.Time) string {
	return dt.Format("2006-01-02T15:04:05")
}

func ParseTimestamp(dtStr string) (time.Time, error) {
	return time.Parse("2006-01-02T15:04:05", dtStr)
}

func Now() time.Time {
	return time.Now()
}
