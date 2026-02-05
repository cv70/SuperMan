package infra

import (
	"context"
	"superman/config"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

func NewDB(ctx context.Context, c *config.DatabaseConfig) (*gorm.DB, error) {
	db, err := gorm.Open(sqlite.Open(c.DBName+".db"), &gorm.Config{})
	return db, err
}
