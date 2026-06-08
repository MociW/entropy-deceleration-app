-- migrate:up



INSERT INTO categorization_config (`key`, `value`, `description`) VALUES
    ('confidence_threshold', 0.20, 'Minimum cosine similarity to accept a category (lower = more tolerant)'),
    ('gap_threshold', 0.03, 'Minimum gap between best and second-best category to be considered Clear'),
    ('eff_threshold', 0.38, 'Minimum cosine similarity to flag a title as efficiency-related');


-- INSERT INTO efficiency_keyword_groups (id, group_order, label) VALUES
--     (UUID(), 0, 'Physics & Thermodynamics'),
--     (UUID(), 1, 'Circular Economy & Waste'),
--     (UUID(), 2, 'Energy & Resource Efficiency'),
--     (UUID(), 3, 'Process & Operational Efficiency'),
--     (UUID(), 4, 'Agricultural & Water Efficiency'),
--     (UUID(), 5, 'Decarbonization & Net Zero'),
--     (UUID(), 6, 'Grid & Power Distribution');




-- Group 0: Physics & Thermodynamics
-- INSERT INTO efficiency_keywords (id, group_id, keyword)
-- SELECT UUID(), g.id, kw.keyword
-- FROM efficiency_keyword_groups g,
-- (VALUES
--     ROW('entropy'), ROW('reduction'), ROW('exergy'), ROW('thermodynamic'),
--     ROW('heat loss'), ROW('thermal insulation'), ROW('perlambatan entropi'),
--     ROW('eksergi'), ROW('termodinamika'), ROW('pengurangan rugi panas'),
--     ROW('isolasi termal')
-- ) AS kw(keyword)
-- WHERE g.group_order = 0;

-- Group 1: Circular Economy & Waste
-- INSERT INTO efficiency_keywords (id, group_id, keyword)
-- SELECT UUID(), g.id, kw.keyword
-- FROM efficiency_keyword_groups g,
-- (VALUES
--     ROW('circularity'), ROW('waste reduction'), ROW('recovery'),
--     ROW('zero waste'), ROW('biomass utilisation'), ROW('waste valorisation'),
--     ROW('sirkularitas'), ROW('daur ulang'), ROW('pemulihan material'),
--     ROW('tanpa limbah'), ROW('pemanfaatan limbah biomassa'),
--     ROW('konversi sampah'), ROW('valorisasi limbah'),
--     ROW('pengolahan limbah'), ROW('ekonomi sirkular'),
--     ROW('efisiensi bahan baku'), ROW('efisiensi material'),
--     ROW('efisiensi sumber daya')
-- ) AS kw(keyword)
-- WHERE g.group_order = 1;

-- -- Group 2: Energy & Resource Efficiency
-- INSERT INTO efficiency_keywords (id, group_id, keyword)
-- SELECT UUID(), g.id, kw.keyword
-- FROM efficiency_keyword_groups g,
-- (VALUES
--     ROW('energy efficiency'), ROW('fuel saving'), ROW('specific consumption'),
--     ROW('heat rate'), ROW('thermal efficiency'), ROW('water efficiency'),
--     ROW('irrigation efficiency'), ROW('agricultural efficiency'),
--     ROW('peningkatan efisiensi energi'), ROW('penghematan bahan bakar'),
--     ROW('efisiensi termal'), ROW('konservasi energi'),
--     ROW('efisiensi sistem energi'), ROW('efisiensi proses produksi'),
--     ROW('efisiensi air'), ROW('efisiensi irigasi'),
--     ROW('efisiensi pertanian'), ROW('optimalisasi penggunaan air'),
--     ROW('efisiensi sumber daya')
-- ) AS kw(keyword)
-- WHERE g.group_order = 2;

-- Group 3: Process & Operational Efficiency
-- INSERT INTO efficiency_keywords (id, group_id, keyword)
-- SELECT UUID(), g.id, kw.keyword
-- FROM efficiency_keyword_groups g,
-- (VALUES
--     ROW('improving construction efficiency'), ROW('increasing project efficiency'),
--     ROW('meningkatkan efisiensi pembangunan'), ROW('meningkatkan efektivitas proyek'),
--     ROW('mengoptimalkan efisiensi konstruksi'), ROW('efisiensi pelaksanaan proyek'),
--     ROW('efisiensi waktu pembangunan'), ROW('efisiensi biaya proyek'),
--     ROW('efisiensi pelaksanaan konstruksi'), ROW('meningkatkan efisiensi produksi'),
--     ROW('meningkatkan produktivitas manufaktur')
-- ) AS kw(keyword)
-- WHERE g.group_order = 3;

-- Group 4: Agricultural & Water Efficiency
-- INSERT INTO efficiency_keywords (id, group_id, keyword)
-- SELECT UUID(), g.id, kw.keyword
-- FROM efficiency_keyword_groups g,
-- (VALUES
--     ROW('water saving'), ROW('irrigation efficiency'), ROW('agricultural productivity'),
--     ROW('smart irrigation'), ROW('precision agriculture'), ROW('water conservation'),
--     ROW('efisiensi irigasi'), ROW('pertanian cerdas'), ROW('optimalisasi air irigasi'),
--     ROW('konservasi air pertanian'), ROW('produktivitas pertanian'),
--     ROW('penghematan air irigasi'), ROW('efisiensi penggunaan air pertanian'),
--     ROW('peningkatan efisiensi pertanian'), ROW('sistem irigasi efisien'),
--     ROW('optimalisasi irigasi'), ROW('efisiensi sumber daya air')
-- ) AS kw(keyword)
-- WHERE g.group_order = 4;

-- Group 5: Decarbonization & Net Zero
-- INSERT INTO efficiency_keywords (id, group_id, keyword)
-- SELECT UUID(), g.id, kw.keyword
-- FROM efficiency_keyword_groups g,
-- (VALUES
--     ROW('net zero'), ROW('transition'), ROW('decarbonization'),
--     ROW('carbon neutral'), ROW('green infrastructure'), ROW('low carbon'),
--     ROW('emission reduction'), ROW('clean energy transition'),
--     ROW('net zero transisi'), ROW('dekarbonisasi'), ROW('infrastruktur hijau'),
--     ROW('rendah karbon'), ROW('transisi energi bersih'),
--     ROW('pengurangan emisi karbon'), ROW('bangunan hijau'),
--     ROW('gedung rendah karbon')
-- ) AS kw(keyword)
-- WHERE g.group_order = 5;

-- Group 6: Grid & Power Distribution
-- INSERT INTO efficiency_keywords (id, group_id, keyword)
-- SELECT UUID(), g.id, kw.keyword
-- FROM efficiency_keyword_groups g,
-- (VALUES
--     ROW('grid efficiency'), ROW('distribution efficiency'), ROW('power quality'),
--     ROW('efisiensi jaringan distribusi'), ROW('efisiensi jaringan listrik'),
--     ROW('kapasitas hosting'), ROW('pengurangan deviasi tegangan'),
--     ROW('reduksi rugi daya'), ROW('efisiensi transmisi listrik'),
--     ROW('peningkatan kapasitas jaringan distribusi tenaga listrik')
-- ) AS kw(keyword)
-- WHERE g.group_order = 6;



-- INSERT INTO efficiency_cue_words (id, word) VALUES
--     (UUID(), 'efisiensi'),
--     (UUID(), 'efficiency'),
--     (UUID(), 'efektivitas'),
--     (UUID(), 'effectiveness'),
--     (UUID(), 'produktivitas'),
--     (UUID(), 'productivity'),
--     (UUID(), 'optimalisasi'),
--     (UUID(), 'optimization'),
--     (UUID(), 'optimasi'),
--     (UUID(), 'optimizing'),
--     (UUID(), 'optimize'),
--     (UUID(), 'net zero'),
--     (UUID(), 'decarbonization'),
--     (UUID(), 'dekarbonisasi'),
--     (UUID(), 'carbon neutral'),
--     (UUID(), 'rendah karbon'),
--     (UUID(), 'low carbon'),
--     (UUID(), 'green infrastructure'),
--     (UUID(), 'infrastruktur hijau'),
--     (UUID(), 'emission reduction'),
--     (UUID(), 'pengurangan emisi'),
--     (UUID(), 'tegangan'),
--     (UUID(), 'distribusi'),
--     (UUID(), 'kapasitas hosting'),
--     (UUID(), 'rugi daya'),
--     (UUID(), 'transmisi listrik'),
--     (UUID(), 'jaringan listrik'),
--     (UUID(), 'power grid'),
--     (UUID(), 'power quality'),
--     (UUID(), 'grid efficiency');

-- migrate:down
