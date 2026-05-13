-- Reference seed data (use backend/services/seed_data.py for the canonical
-- seed — it correctly hashes passwords. This file is illustrative.)

INSERT INTO roles (role_name) VALUES
  ('Admin'), ('Supervisor'), ('Support Agent'), ('Customer');

INSERT INTO categories (category_name, description) VALUES
  ('Billing Issues',        'Invoices, charges, refunds'),
  ('Service Disruption',    'Outages, slowness, downtime'),
  ('Product Defects',       'Physical or software defects'),
  ('Technical Problems',    'Setup, login, integration issues'),
  ('Delivery Delays',       'Shipping or fulfillment delays'),
  ('Account Issues',        'Profile, access, account changes'),
  ('Customer Service Complaints', 'Concerns with prior support interactions');
