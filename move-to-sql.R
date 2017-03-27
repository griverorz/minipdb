library(bit64)
library(readr)
library(RODBC)
library(RPostgreSQL)
library(jsonlite)

options(digits = 14)

creds <- fromJSON("credentials.json")
drv <- dbDriver("PostgreSQL")

con <- dbConnect(drv,
                 dbname=creds$dbname,
                 host=creds$host,
                 port=creds$port,
                 user=creds$user,
                 password=creds$password); rm(creds)

temp <- tempfile()
url <- "https://www.census.gov/research/data/planning_database/2015/docs/PDB_Block_Group_2015-07-28.zip"
download.file(url, temp)
pdb <- read.csv(unz(temp, "tmp.csv"))
unlink(temp)

pdb$GIDBG <- as.integer64(pdb$GIDBG)

dbWriteTable(con,
             "pdb", 
             value=pdb,
             append=FALSE,
             row.names=FALSE)

dbGetQuery(con, "CREATE INDEX GIDBG_idx ON pdb (\"GIDBG\");")
dbGetQuery(con, "CREATE INDEX Tract_idx ON pdb (\"Tract\");")
dbGetQuery(con, "CREATE INDEX Block_Group_idx ON pdb (\"Block_Group\");")

