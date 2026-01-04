import csv
import logging
import os
from datetime import datetime
from pathlib import Path

from omegaconf import DictConfig

from src.model.models import Asset, AssetValue, MonthlyTransaction
from src.service.finance_service import FinanceService


class Ingestion:
    """Handles migration from CSV to database."""

    def __init__(self, service: FinanceService, config: DictConfig):
        """
        Initialize migrator.

        Args:
            service: FinanceService instance
            config: Hydra configuration
        """
        self.service = service
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.batch_size = 100  # Number of rows to insert at once

    def migrate(self):
        """Execute the migration from CSV to database."""
        csv_path = os.path.join(self.config.csv_import.folder, self.config.csv_import.file_path)
        csv_path = os.path.join(os.getcwd(), csv_path)

        self.logger.info(f"Starting migration from {csv_path}")

        #  Check if file exists
        if not Path(csv_path).exists():
            self.logger.error(f"CSV file not found: {csv_path}")
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Step 1: Create or get assets (cached)
        asset_map = self._create_assets()

        # Step 2: Read and prepare data
        transactions, asset_values = self._read_csv(csv_path, asset_map)

        # Step 3: Bulk insert
        self._bulk_insert(transactions, asset_values)

        self.logger.info(f"✓ Successfully migrated {len(transactions)} rows")

    def _create_assets(self) -> dict[str, Asset]:
        """
        Create or get assets from configuration.

        Returns:
            Dictionary mapping CSV prefix to Asset object
        """
        asset_map = {}

        # Check if assets already exist (avoid duplicates)
        existing_assets = {a.name: a for a in self.service.get_all_assets()}

        for mapping in self.config.asset_mappings:
            if mapping.name in existing_assets:
                asset = existing_assets[mapping.name]
                self.logger.info(f"Using existing asset: {mapping.name}")
            else:
                self.logger.info(f"Creating asset: {mapping.name} ({mapping.type})")
                asset = self.service.add_asset(name=mapping.name, asset_type=mapping.type, currency=mapping.currency)

            asset_map[mapping.csv_prefix] = asset

        return asset_map

    def _read_csv(self, csv_path: str, asset_map: dict[str, Asset]) -> tuple[list[dict], list[dict]]:
        """
        Read CSV and prepare data for bulk insert.

        Args:
            csv_path: Path to CSV file
            asset_map: Mapping of CSV prefix to Asset objects

        Returns:
            Tuple of (transactions, asset_values) as list of dicts
        """
        date_format = self.config.csv_import.date_format
        transactions = []
        asset_values = []

        with open(csv_path) as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=1):
                try:
                    date = datetime.strptime(row["Date"], date_format)

                    # Prepare transaction data
                    transactions.append(
                        {
                            "date": date,
                            "income": float(row["Income"]),
                            "expenses": float(row["Expenses"]),
                            "cash": float(row["Cash"]),
                        }
                    )

                    # Prepare asset values data
                    for prefix, asset in asset_map.items():
                        # Determine column names
                        if prefix == "Crypto":
                            invested_col = "Crypto Invested"
                            countervalue_col = "Crypto Countervalue"
                        else:
                            invested_col = f"{prefix} Invested"
                            countervalue_col = f"{prefix} Countervalue"

                        asset_values.append(
                            {
                                "date": date,
                                "asset_id": asset.asset_id,
                                "amount_invested": float(row[invested_col]),
                                "countervalue": float(row[countervalue_col]),
                            }
                        )

                    if row_num % 100 == 0:
                        self.logger.info(f"Read {row_num} rows...")

                except Exception as e:
                    self.logger.error(f"Error reading row {row_num}: {e}")
                    self.logger.error(f"Row data: {row}")
                    raise

        self.logger.info(f"✓ Read {len(transactions)} transactions and {len(asset_values)} asset values")
        return transactions, asset_values

    def _bulk_insert(self, transactions: list[dict], asset_values: list[dict]):
        """
        Perform bulk insert of transactions and asset values.

        Args:
            transactions: List of transaction dicts
            asset_values: List of asset value dicts
        """
        with self.service.get_session() as session:
            # Bulk insert transactions
            self.logger.info("Inserting transactions...")

            for i in range(0, len(transactions), self.batch_size):
                batch = transactions[i : i + self.batch_size]

                # Create MonthlyTransaction objects
                objects = [MonthlyTransaction(**data) for data in batch]

                # Bulk insert
                session.bulk_save_objects(objects)
                session.flush()

                if (i + self.batch_size) % 500 == 0:
                    self.logger.info(f"  Inserted {i + self.batch_size} transactions...")

            session.commit()
            self.logger.info(f"✓ Inserted {len(transactions)} transactions")

            # Bulk insert asset values
            self.logger.info("Inserting asset values...")

            for i in range(0, len(asset_values), self.batch_size):
                batch = asset_values[i : i + self.batch_size]

                # Create AssetValue objects
                objects = [AssetValue(**data) for data in batch]

                # Bulk insert
                session.bulk_save_objects(objects)
                session.flush()

                if (i + self.batch_size) % 500 == 0:
                    self.logger.info(f"  Inserted {i + self.batch_size} asset values...")

            session.commit()
            self.logger.info(f"✓ Inserted {len(asset_values)} asset values")
