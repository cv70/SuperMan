package infra

import (
	"context"
	"superman/config"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

func NewDB(ctx context.Context, c *config.DBConfig) (*gorm.DB, error) {
	dsn := c.Name + ".db"
	println(dsn)
	db, err := gorm.Open(sqlite.Open(dsn), &gorm.Config{})
	return db, err
}
